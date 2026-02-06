from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class Label(Base, TimestampMixin):
    __tablename__ = "labels"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    stored_filepath: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    batch_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("batch_jobs.id"), nullable=True
    )

    analysis: Mapped["AnalysisResult"] = relationship(back_populates="label")
