from .llm import embed_text, answer_question
from .vectordb import search_segments
from typing import Generator


def query_video(video_id: str, question: str, top_k: int = 5) -> Generator[str, None, None]:
    """
    Full RAG pipeline:
    1. Embed the question
    2. Retrieve top-k segments from vector DB
    3. Stream LLM answer with timestamps
    Yields SSE-compatible text chunks, then a final JSON event.
    """
    # 1. Embed query
    query_embedding = embed_text(question)

    # 2. Retrieve segments
    segments = search_segments(video_id, query_embedding, top_k=top_k)

    if not segments:
        yield "data: No relevant segments found for this question.\n\n"
        yield "data: [DONE]\n\n"
        return

    # 3. Stream answer
    for chunk in answer_question(question, segments):
        yield f"data: {chunk}\n\n"

    # 4. Send cited timestamps as final event
    import json
    citations = [
        {"start_time": seg["start_time"], "end_time": seg["end_time"], "text": seg["fused_text"][:120]}
        for seg in segments
    ]
    yield f"event: citations\ndata: {json.dumps(citations)}\n\n"
    yield "data: [DONE]\n\n"
