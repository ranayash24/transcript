import uuid
from sqlalchemy import String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(String, ForeignKey("videos.id"), nullable=False, index=True)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    frame_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    fused_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    keyframe_url: Mapped[str | None] = mapped_column(String, nullable=True)

    video: Mapped["Video"] = relationship("Video", back_populates="segments")
