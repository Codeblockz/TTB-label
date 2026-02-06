from datetime import datetime

from pydantic import BaseModel


class LabelResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    batch_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
