"""
Main pipeline orchestrator — runs as a Celery task.
Steps: download → ffmpeg → whisper → caption → fusion → embed → done
"""
import os
import uuid
import tempfile
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .celery_app import celery_app
from .ffmpeg_task import extract_frames_and_audio, get_video_duration
from .whisper_task import transcribe
from .caption_task import caption_frames
from .fusion_task import fuse_segments
from .embed_task import embed_and_index
from ..services.storage import download_file, upload_file, get_signed_url
from ..models import Video, Segment, Job
from ..models.video import VideoStatus
from ..models.job import JobStatus
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _sync_db_session():
    # Convert async URL to sync (strip +asyncpg driver)
    sync_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(sync_url)
    return sessionmaker(bind=engine)()


def _update_job(session, job_id: str, status: JobStatus, step: str, pct: int, error: str = None):
    job = session.query(Job).filter_by(id=job_id).first()
    if job:
        job.status = status
        job.current_step = step
        job.progress_pct = pct
        if error:
            job.error_message = error
        session.commit()


def _update_video_status(session, video_id: str, status: VideoStatus):
    video = session.query(Video).filter_by(id=video_id).first()
    if video:
        video.status = status
        session.commit()


@celery_app.task(bind=True, max_retries=2)
def run_pipeline(self, video_id: str, job_id: str, storage_key: str):
    session = _sync_db_session()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # --- Step 1: Download video ---
            _update_job(session, job_id, JobStatus.running, "Downloading", 5)
            video_path = os.path.join(tmpdir, "video.mp4")
            download_file(storage_key, video_path)

            # --- Step 2: FFmpeg extraction ---
            _update_job(session, job_id, JobStatus.running, "Extracting frames", 15)
            _update_video_status(session, video_id, VideoStatus.extracting)
            extracted = extract_frames_and_audio(video_path, tmpdir)
            duration = get_video_duration(video_path)

            # Update duration on video record
            video = session.query(Video).filter_by(id=video_id).first()
            if video:
                video.duration_seconds = duration
                session.commit()

            # --- Step 3: Whisper transcription ---
            _update_job(session, job_id, JobStatus.running, "Transcribing audio", 30)
            _update_video_status(session, video_id, VideoStatus.transcribing)
            words = transcribe(extracted["audio_path"])

            # --- Step 4: Frame captioning (with graceful fallback) ---
            _update_job(session, job_id, JobStatus.running, "Captioning frames", 50)
            _update_video_status(session, video_id, VideoStatus.captioning)
            try:
                captioned = caption_frames(extracted["frames"])
            except Exception as e:
                logger.warning(f"Frame captioning failed ({e}), continuing with transcript only")
                captioned = [{**f, "caption": ""} for f in extracted["frames"]]

            # Upload keyframes to storage
            for frame in captioned:
                key = f"videos/{video_id}/frames/{os.path.basename(frame['path'])}"
                upload_file(frame["path"], key, "image/jpeg")
                frame["keyframe_url"] = key

            # --- Step 5: Fusion ---
            _update_job(session, job_id, JobStatus.running, "Fusing segments", 70)
            fused = fuse_segments(words, captioned, duration)

            # Persist segments to DB
            db_segments = []
            for seg in fused:
                seg_id = str(uuid.uuid4())
                db_seg = Segment(
                    id=seg_id,
                    video_id=video_id,
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                    transcript_text=seg["transcript_text"],
                    frame_caption=seg["frame_caption"],
                    fused_text=seg["fused_text"],
                    keyframe_url=seg.get("keyframe_url", ""),
                )
                session.add(db_seg)
                seg["id"] = seg_id
                seg["keyframe_url"] = seg.get("keyframe_url", "")
                db_segments.append(seg)
            session.commit()

            # --- Step 6: Embedding + vector indexing ---
            _update_job(session, job_id, JobStatus.running, "Indexing", 85)
            _update_video_status(session, video_id, VideoStatus.indexing)
            embed_and_index(video_id, db_segments)

            # --- Done ---
            _update_job(session, job_id, JobStatus.done, "Ready", 100)
            _update_video_status(session, video_id, VideoStatus.ready)
            logger.info(f"Pipeline complete for video {video_id}")

    except Exception as exc:
        logger.exception(f"Pipeline failed for video {video_id}: {exc}")
        _update_job(session, job_id, JobStatus.failed, "Error", 0, str(exc))
        _update_video_status(session, video_id, VideoStatus.error)
        raise
    finally:
        session.close()
