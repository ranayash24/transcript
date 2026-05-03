import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class VideoStatus(str, enum.Enum):
    uploading = "uploading"
    extracting = "extracting"
    transcribing = "transcribing"
    captioning = "captioning"
    indexing = "indexing"
    ready = "ready"
    error = "error"


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    storage_url: Mapped[str] = mapped_column(String, nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[VideoStatus] = mapped_column(SAEnum(VideoStatus), default=VideoStatus.uploading)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    segments: Mapped[list["Segment"]] = relationship("Segment", back_populates="video", cascade="all, delete-orphan")
    job: Mapped["Job | None"] = relationship("Job", back_populates="video", uselist=False)
