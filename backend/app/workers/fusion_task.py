"""
Fusion task: merge Whisper word-level transcript + frame captions
into fixed time-window segments.
"""
from ..config import get_settings


def fuse_segments(
    words: list[dict],        # from whisper: [{start, end, text}]
    captioned_frames: list[dict],  # [{timestamp, caption, path, ...}]
    duration: float,
) -> list[dict]:
    """
    Returns list of fused segments:
    [{start_time, end_time, transcript_text, frame_caption, fused_text, keyframe_path}]
    """
    settings = get_settings()
    window = settings.segment_window_seconds

    segments = []
    t = 0.0
    while t < duration:
        end = min(t + window, duration)

        # Collect words in this window
        window_words = [w for w in words if w["start"] >= t and w["start"] < end]
        transcript_text = " ".join(w["text"] for w in window_words).strip()

        # Find the best keyframe for this window (closest to window midpoint)
        midpoint = (t + end) / 2
        best_frame = None
        best_dist = float("inf")
        for frame in captioned_frames:
            dist = abs(frame["timestamp"] - midpoint)
            if dist < best_dist:
                best_dist = dist
                best_frame = frame

        frame_caption = best_frame["caption"] if best_frame else ""
        keyframe_path = best_frame.get("path", "") if best_frame else ""

        # Fuse: combine both sources
        parts = []
        if transcript_text:
            parts.append(f"Speech: {transcript_text}")
        if frame_caption:
            parts.append(f"Visual: {frame_caption}")
        fused_text = " | ".join(parts) if parts else ""

        if fused_text:  # Skip empty segments
            segments.append({
                "start_time": t,
                "end_time": end,
                "transcript_text": transcript_text,
                "frame_caption": frame_caption,
                "fused_text": fused_text,
                "keyframe_path": keyframe_path,
            })

        t = end

    return segments
