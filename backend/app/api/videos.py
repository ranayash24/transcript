import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from ..database import get_db
from ..models import Video, Segment, Job
from ..models.video import VideoStatus
from ..models.job import JobStatus
from ..services import storage
from ..config import get_settings
from ..workers.pipeline import run_pipeline

router = APIRouter(prefix="/api/videos", tags=["videos"])
settings = get_settings()

MAX_BYTES = settings.max_video_size_mb * 1024 * 1024
ALLOWED_TYPES = {"video/mp4", "video/quicktime", "video/webm"}


class VideoOut(BaseModel):
    id: str
    filename: str
    status: str
    duration_seconds: float | None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    x_session_id: str = Header(default="anonymous"),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported format: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, f"File exceeds {settings.max_video_size_mb}MB limit")

    video_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    object_key = f"videos/{video_id}/original{os.path.splitext(file.filename)[1]}"

    # Upload to R2
    import io
    storage.upload_fileobj(io.BytesIO(content), object_key, file.content_type)

    # Persist video record
    video = Video(
        id=video_id,
        user_session_id=x_session_id,
        filename=file.filename,
        storage_url=object_key,
        status=VideoStatus.uploading,
    )
    db.add(video)

    # Create job record
    job = Job(id=job_id, video_id=video_id, status=JobStatus.pending, current_step="Queued", progress_pct=0)
    db.add(job)
    await db.commit()

    # Enqueue pipeline
    run_pipeline.delay(video_id, job_id, object_key)

    return {
        "video_id": video_id,
        "job_id": job_id,
        "status_url": f"/api/jobs/{job_id}/status",
    }


@router.get("/{video_id}", response_model=VideoOut)
async def get_video(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")
    return VideoOut(
        id=video.id,
        filename=video.filename,
        status=video.status.value,
        duration_seconds=video.duration_seconds,
        created_at=video.created_at.isoformat(),
    )


@router.get("/{video_id}/segments")
async def get_segments(
    video_id: str,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    result = await db.execute(
        select(Segment)
        .where(Segment.video_id == video_id)
        .order_by(Segment.start_time)
        .offset(offset)
        .limit(limit)
    )
    segments = result.scalars().all()
    return [
        {
            "id": s.id,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "transcript_text": s.transcript_text,
            "frame_caption": s.frame_caption,
            "fused_text": s.fused_text,
            "keyframe_url": s.keyframe_url,
        }
        for s in segments
    ]


@router.get("/{video_id}/playback-url")
async def playback_url(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")
    url = storage.get_signed_url(video.storage_url)
    return {"url": url}
