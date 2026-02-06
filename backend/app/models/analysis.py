import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, generate_uuid


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING_OCR = "processing_ocr"
    PROCESSING_COMPLIANCE = "processing_compliance"
    COMPLETED = "completed"
    FAILED = "failed"


class OverallVerdict(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNINGS = "warnings"


class AnalysisResult(Base, TimestampMixin):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    label_id: Mapped[str] = mapped_column(
        String, ForeignKey("labels.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False
    )

    # OCR results
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Compliance results
    compliance_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_verdict: Mapped[str | None] = mapped_column(
        Enum(OverallVerdict), nullable=True
    )
    compliance_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    detected_beverage_type: Mapped[str | None] = mapped_column(String, nullable=True)
    detected_brand_name: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    label: Mapped["Label"] = relationship(back_populates="analysis")
