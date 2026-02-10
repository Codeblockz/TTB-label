import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


async def save_upload(file: UploadFile) -> tuple[str, int]:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "upload").suffix
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = upload_dir / stored_name

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)  # 1 MB chunks
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")
        chunks.append(chunk)

    content = b"".join(chunks)
    file_size = len(content)

    with open(stored_path, "wb") as f:
        f.write(content)

    return str(stored_path), file_size


def get_upload_path(filename: str) -> str:
    return os.path.join(settings.upload_dir, filename)
