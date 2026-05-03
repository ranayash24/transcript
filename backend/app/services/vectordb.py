from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    QueryRequest,
)
from ..config import get_settings

VECTOR_DIM = 3072  # Gemini gemini-embedding-001 output dimension


def _get_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)


def ensure_collection() -> None:
    settings = get_settings()
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )


def upsert_segments(
    video_id: str,
    segments: list[dict],
) -> None:
    settings = get_settings()
    client = _get_client()
    points = [
        PointStruct(
            id=seg["id"],
            vector=seg["embedding"],
            payload={
                "video_id": video_id,
                "segment_id": seg["id"],
                "start_time": seg["start_time"],
                "end_time": seg["end_time"],
                "fused_text": seg["fused_text"],
                "keyframe_url": seg.get("keyframe_url", ""),
            },
        )
        for seg in segments
    ]
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def search_segments(video_id: str, query_vector: list[float], top_k: int = 5) -> list[dict]:
    settings = get_settings()
    client = _get_client()

    # Use query_points (new API) with fallback to search (old API)
    try:
        results = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
            ),
            limit=top_k,
            with_payload=True,
        ).points
    except AttributeError:
        results = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
            ),
            limit=top_k,
            with_payload=True,
        )

    return [
        {
            "score": r.score,
            "start_time": r.payload["start_time"],
            "end_time": r.payload["end_time"],
            "fused_text": r.payload["fused_text"],
            "keyframe_url": r.payload.get("keyframe_url", ""),
            "segment_id": r.payload["segment_id"],
        }
        for r in results
    ]


def delete_video_segments(video_id: str) -> None:
    settings = get_settings()
    client = _get_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
        ),
    )
