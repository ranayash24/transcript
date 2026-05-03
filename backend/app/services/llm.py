"""
LLM service using Google Gemini (free tier).
Uses the new google-genai SDK (google.generativeai is deprecated).
- Vision/captioning: models/gemini-2.5-flash      (vision capable, 20 req/day free)
- Embeddings:        models/gemini-embedding-001   (3072 dims)
- Q&A streaming:     models/gemini-2.5-flash-lite  (separate quota, text only)
"""
import base64
from google import genai
from google.genai import types
from ..config import get_settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=get_settings().gemini_api_key)
    return _client


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns a 768-dim vector."""
    result = _get_client().models.embed_content(
        model="models/gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return result.embeddings[0].values


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts, one call each (batch API not in free tier)."""
    return [embed_text(t) for t in texts]


# ---------------------------------------------------------------------------
# Frame captioning
# ---------------------------------------------------------------------------

def caption_frame(image_path: str) -> str:
    """Caption a keyframe image using Gemini 1.5 Flash vision."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    prompt_text = (
        "Describe what is visible in this video frame in 1-2 sentences. "
        "Focus on: people, text on screen, objects, actions, and any information visible. "
        "Be specific and factual."
    )
    response = _get_client().models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text=prompt_text),
        ],
    )
    return response.text.strip()


# ---------------------------------------------------------------------------
# Q&A streaming
# ---------------------------------------------------------------------------

def answer_question(question: str, context_segments: list[dict]):
    """
    Stream a RAG answer. Yields text chunks via Gemini streaming.
    """
    context_text = "\n\n".join(
        f"[{_fmt_time(seg['start_time'])} – {_fmt_time(seg['end_time'])}]\n{seg['fused_text']}"
        for seg in context_segments
    )

    prompt = (
        "You are a video intelligence assistant. "
        "Answer the user's question using only the provided timestamped video segments. "
        "Always cite timestamps in your answer using the format [MM:SS]. "
        "If the answer is not in the segments, say so.\n\n"
        f"VIDEO SEGMENTS:\n{context_text}\n\n"
        f"QUESTION: {question}"
    )

    for chunk in _get_client().models.generate_content_stream(
        model="models/gemini-2.5-flash-lite",
        contents=prompt,
    ):
        if chunk.text:
            yield chunk.text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"
