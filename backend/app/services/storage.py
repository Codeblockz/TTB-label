import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


async def save_upload(file: UploadFile) -> tuple[str, int]:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "upload").suffix
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = upload_dir / stored_name

    content = await file.read()
    file_size = len(content)

    with open(stored_path, "wb") as f:
        f.write(content)

    return str(stored_path), file_size


def get_upload_path(filename: str) -> str:
    return os.path.join(settings.upload_dir, filename)
