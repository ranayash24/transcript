from celery import Celery
from ..config import get_settings

settings = get_settings()

celery_app = Celery(
    "vsi_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.pipeline",
        "app.workers.ffmpeg_task",
        "app.workers.whisper_task",
        "app.workers.caption_task",
        "app.workers.fusion_task",
        "app.workers.embed_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    # Required on macOS — prevents fork() crash with Objective-C runtime
    worker_pool="solo",
)
