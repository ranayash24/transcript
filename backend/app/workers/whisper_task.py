"""
Whisper ASR task: transcribe audio and return word-level timestamps.
"""
from faster_whisper import WhisperModel
from ..config import get_settings

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        settings = get_settings()
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> list[dict]:
    """
    Returns list of word-level segments:
    [{"start": float, "end": float, "text": str}, ...]
    """
    model = _get_model()
    segments, _info = model.transcribe(audio_path, word_timestamps=True)

    words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                words.append({
                    "start": word.start,
                    "end": word.end,
                    "text": word.word,
                })
        else:
            # No word-level data, fall back to segment level
            words.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            })
    return words
