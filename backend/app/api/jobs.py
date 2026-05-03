from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}/status")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job.id,
        "video_id": job.video_id,
        "status": job.status.value,
        "current_step": job.current_step,
        "progress_pct": job.progress_pct,
        "error": job.error_message,
    }
