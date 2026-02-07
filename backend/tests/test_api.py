import io

import pytest
import pytest_asyncio
from httpx import AsyncClient


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_upload_single_label(client: AsyncClient):
    response = await client.post(
        "/api/analysis/single",
        files={"file": ("test_label.png", io.BytesIO(PNG_BYTES), "image/png")},
        data={"brand_name": "Test Brand"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data


@pytest.mark.asyncio
async def test_upload_single_requires_brand_name(client: AsyncClient):
    response = await client.post(
        "/api/analysis/single",
        files={"file": ("test_label.png", io.BytesIO(PNG_BYTES), "image/png")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_single_with_all_application_details(client: AsyncClient):
    response = await client.post(
        "/api/analysis/single",
        files={"file": ("test_label.png", io.BytesIO(PNG_BYTES), "image/png")},
        data={
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "alcohol_content": "45% Alc./Vol.",
            "net_contents": "750 mL",
            "bottler_name_address": "Old Tom Distillery, Louisville, Kentucky",
            "country_of_origin": "USA",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data


@pytest.mark.asyncio
async def test_upload_rejects_non_image(client: AsyncClient):
    response = await client.post(
        "/api/analysis/single",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        data={"brand_name": "Test Brand"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_analysis_not_found(client: AsyncClient):
    response = await client.get("/api/analysis/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_analyses_empty(client: AsyncClient):
    response = await client.get("/api/analysis/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_analysis_after_upload(client: AsyncClient):
    upload_resp = await client.post(
        "/api/analysis/single",
        files={"file": ("label.png", io.BytesIO(PNG_BYTES), "image/png")},
        data={"brand_name": "Test Brand"},
    )
    analysis_id = upload_resp.json()["analysis_id"]

    get_resp = await client.get(f"/api/analysis/{analysis_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == analysis_id
    assert data["status"] in ["pending", "processing_ocr", "processing_compliance", "completed", "failed"]
    assert data["application_details"]["brand_name"] == "Test Brand"


@pytest.mark.asyncio
async def test_batch_upload_with_csv(client: AsyncClient):
    csv_content = (
        "filename,brand_name,class_type,alcohol_content\n"
        "label1.png,Brand A,Bourbon,40% ABV\n"
        "label2.png,Brand B,Wine,12% ABV\n"
    )

    response = await client.post(
        "/api/batch/upload",
        files=[
            ("files", ("label1.png", io.BytesIO(PNG_BYTES), "image/png")),
            ("files", ("label2.png", io.BytesIO(PNG_BYTES), "image/png")),
            ("csv_file", ("details.csv", io.BytesIO(csv_content.encode()), "text/csv")),
        ],
    )
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert data["total_labels"] == 2
