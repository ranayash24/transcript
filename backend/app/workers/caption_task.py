"""
Caption task: generate captions for keyframes using Gemini Vision.

Free-tier strategy:
- Caption at most MAX_CAPTIONS_PER_VIDEO unique frames per video (default 3)
- Remaining frames inherit the nearest captioned frame's description
- This keeps Gemini vision calls low (3 per video = 6 videos/day on free tier)
- Transcript-only segments still work great for Q&A
"""
import time
import logging
import imagehash
from PIL import Image
from ..services.llm import caption_frame
from ..config import get_settings

logger = logging.getLogger(__name__)

MAX_CAPTIONS_PER_VIDEO = 3   # Max Gemini vision calls per video
RETRY_WAIT_SECONDS = 15      # Wait between calls to respect per-minute limit
MAX_RETRIES = 3


def _caption_with_retry(image_path: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            return caption_frame(image_path)
        except Exception as e:
            if ("RESOURCE_EXHAUSTED" in str(e) or "429" in str(e)) and attempt < MAX_RETRIES - 1:
                wait = RETRY_WAIT_SECONDS * (attempt + 1)
                logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def caption_frames(frames: list[dict]) -> list[dict]:
    """
    Caption keyframes, capped at MAX_CAPTIONS_PER_VIDEO Gemini API calls.
    All other frames reuse the nearest captioned frame's description.

    Returns same list with 'caption' field added to each frame.
    """
    if not frames:
        return frames

    # Step 1: deduplicate by pHash to find unique visual frames
    seen_hashes: list[imagehash.ImageHash] = []
    unique_indices: list[int] = []

    for i, frame in enumerate(frames):
        try:
            img = Image.open(frame["path"])
            phash = imagehash.phash(img)
            if not any(abs(phash - h) < 8 for h in seen_hashes):
                seen_hashes.append(phash)
                unique_indices.append(i)
        except Exception:
            continue

    # Step 2: pick up to MAX_CAPTIONS_PER_VIDEO evenly spaced unique frames to caption
    step = max(1, len(unique_indices) // MAX_CAPTIONS_PER_VIDEO)
    to_caption = set(unique_indices[::step][:MAX_CAPTIONS_PER_VIDEO])

    logger.info(f"{len(frames)} total frames, {len(unique_indices)} unique, "
                f"captioning {len(to_caption)} with Gemini")

    # Step 3: caption selected frames, pace calls
    captions: dict[int, str] = {}
    call_count = 0
    for i in sorted(to_caption):
        if call_count > 0:
            time.sleep(RETRY_WAIT_SECONDS)
        try:
            captions[i] = _caption_with_retry(frames[i]["path"])
            logger.info(f"Captioned frame at {frames[i]['timestamp']:.1f}s")
        except Exception as e:
            logger.warning(f"Captioning failed for frame {i}, skipping: {e}")
            captions[i] = ""
        call_count += 1

    # Step 4: assign captions — uncaptioned frames inherit nearest captioned frame
    results = []
    last_caption = ""
    captioned_positions = sorted(captions.keys())

    for i, frame in enumerate(frames):
        if i in captions:
            last_caption = captions[i]
            caption = last_caption
        else:
            # Find nearest captioned frame's text
            if captioned_positions:
                nearest = min(captioned_positions, key=lambda p: abs(p - i))
                caption = captions.get(nearest, "")
            else:
                caption = ""

        results.append({**frame, "caption": caption})

    return results
