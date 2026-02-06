import enum

from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_uuid


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJob(Base, TimestampMixin):
    __tablename__ = "batch_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    status: Mapped[str] = mapped_column(
        Enum(BatchStatus), default=BatchStatus.PENDING, nullable=False
    )
    total_labels: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_labels: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_labels: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
