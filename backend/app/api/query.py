from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from ..database import get_db
from ..models import Video
from ..models.video import VideoStatus
from ..services.rag import query_video

router = APIRouter(prefix="/api/videos", tags=["query"])


class QueryRequest(BaseModel):
    question: str


@router.post("/{video_id}/query")
async def query(
    video_id: str,
    body: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")
    if video.status != VideoStatus.ready:
        raise HTTPException(400, f"Video is not ready yet (status: {video.status.value})")

    def generate():
        yield from query_video(video_id, body.question)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
