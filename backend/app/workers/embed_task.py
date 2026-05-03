"""
Embed task: generate embeddings for fused segments and upsert into vector DB.
"""
from ..services.llm import embed_texts
from ..services.vectordb import upsert_segments, ensure_collection


def embed_and_index(video_id: str, segments: list[dict]) -> None:
    """
    segments: list from fusion_task with fused_text.
    Embeds all fused_texts in batch, then upserts into Qdrant.
    """
    ensure_collection()

    texts = [seg["fused_text"] for seg in segments]
    embeddings = embed_texts(texts)

    enriched = []
    for seg, embedding in zip(segments, embeddings):
        enriched.append({
            "id": seg["id"],
            "start_time": seg["start_time"],
            "end_time": seg["end_time"],
            "fused_text": seg["fused_text"],
            "embedding": embedding,
            "keyframe_url": seg.get("keyframe_url", ""),
        })

    upsert_segments(video_id, enriched)
