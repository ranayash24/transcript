"""
FFmpeg task: extract keyframes and strip audio from a video file.
"""
import os
import json
import subprocess
import tempfile
from pathlib import Path
from ..config import get_settings

settings = get_settings()


def extract_frames_and_audio(video_path: str, output_dir: str) -> dict:
    """
    Returns:
        {
          "frames": [{"path": str, "timestamp": float}, ...],
          "audio_path": str
        }
    """
    os.makedirs(output_dir, exist_ok=True)
    frames_dir = os.path.join(output_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, "audio.wav")

    # Strip audio track
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            audio_path,
        ],
        check=True,
        capture_output=True,
    )

    # Extract keyframes using scene change detection
    scene_output = os.path.join(frames_dir, "frame_%06d.jpg")
    threshold = settings.scene_change_threshold
    interval = settings.frame_interval_seconds

    # Try scene-change detection first
    scene_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',scale=512:-1",
        "-vsync", "vfr",
        "-q:v", "3",
        scene_output,
    ]
    result = subprocess.run(scene_cmd, capture_output=True)

    frame_paths = sorted(Path(frames_dir).glob("frame_*.jpg"))

    # Fall back to fixed-interval if too few frames detected
    if len(frame_paths) < 5:
        for fp in frame_paths:
            fp.unlink()
        fallback_cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", f"fps=1/{interval},scale=512:-1",
            "-q:v", "3",
            scene_output,
        ]
        subprocess.run(fallback_cmd, check=True, capture_output=True)
        frame_paths = sorted(Path(frames_dir).glob("frame_*.jpg"))

    # Get timestamps for each frame using ffprobe
    probe_result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "frame=pkt_pts_time",
            "-of", "json",
            video_path,
        ],
        capture_output=True,
        text=True,
    )
    try:
        frame_data = json.loads(probe_result.stdout)
        all_pts = [float(f["pkt_pts_time"]) for f in frame_data.get("frames", [])]
    except Exception:
        all_pts = []

    # Assign timestamps proportionally if probe data unavailable
    frames = []
    for i, fp in enumerate(frame_paths):
        ts = all_pts[i] if i < len(all_pts) else i * interval
        frames.append({"path": str(fp), "timestamp": ts})

    return {"frames": frames, "audio_path": audio_path}


def get_video_duration(video_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])
