from datetime import datetime

from pydantic import BaseModel

from app.schemas.analysis import AnalysisResponse


class BatchResponse(BaseModel):
    id: str
    status: str
    total_labels: int
    completed_labels: int
    failed_labels: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BatchDetailResponse(BaseModel):
    batch: BatchResponse
    analyses: list[AnalysisResponse]
