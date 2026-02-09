import csv
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.samples import SampleLabel, SampleLabelsResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/samples", tags=["samples"])

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"
GENERATED_DIR = FIXTURES_DIR / "generated"


def _load_hand_crafted() -> list[SampleLabel]:
    csv_path = FIXTURES_DIR / "test_labels.csv"
    if not csv_path.exists():
        return []
    samples = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            samples.append(SampleLabel(
                filename=row["filename"],
                brand_name=row["brand_name"],
                class_type=row["class_type"],
                alcohol_content=row["alcohol_content"],
                net_contents=row["net_contents"],
                bottler_name_address=row["bottler_name_address"],
                country_of_origin=row["country_of_origin"],
                description="Hand-crafted test label",
                expected_verdict="pass",
                image_url=f"/api/samples/{row['filename']}/image",
            ))
    return samples


def _load_openai_generated() -> list[SampleLabel]:
    csv_path = FIXTURES_DIR / "generated_labels.csv"
    if not csv_path.exists():
        return []
    samples = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("generation_method") != "openai":
                continue
            samples.append(SampleLabel(
                filename=row["filename"],
                brand_name=row["brand_name"],
                class_type=row["class_type"],
                alcohol_content=row["alcohol_content"],
                net_contents=row["net_contents"],
                bottler_name_address=row["bottler_name_address"],
                country_of_origin=row["country_of_origin"],
                description=row.get("description", ""),
                expected_verdict=row.get("expected_verdict", "pass"),
                image_url=f"/api/samples/{row['filename']}/image",
            ))
    return samples


@router.get("/", response_model=SampleLabelsResponse)
async def list_samples():
    hand_crafted = _load_hand_crafted()
    openai_generated = _load_openai_generated()
    return SampleLabelsResponse(samples=hand_crafted + openai_generated)


@router.get("/{filename}/image")
async def get_sample_image(filename: str):
    # Path traversal check
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Check hand-crafted fixtures first, then generated
    image_path = FIXTURES_DIR / filename
    if not image_path.exists():
        image_path = GENERATED_DIR / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Sample image not found")

    suffix = image_path.suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    media_type = media_types.get(suffix, "image/png")

    return FileResponse(image_path, media_type=media_type)
