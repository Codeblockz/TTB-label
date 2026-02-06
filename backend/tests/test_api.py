import io

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_upload_single_label(client: AsyncClient):
    # Create a minimal PNG file (1x1 pixel)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    response = await client.post(
        "/api/analysis/single",
        files={"file": ("test_label.png", io.BytesIO(png_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data


@pytest.mark.asyncio
async def test_upload_rejects_non_image(client: AsyncClient):
    response = await client.post(
        "/api/analysis/single",
        files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
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
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
        b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
        b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    upload_resp = await client.post(
        "/api/analysis/single",
        files={"file": ("label.png", io.BytesIO(png_bytes), "image/png")},
    )
    analysis_id = upload_resp.json()["analysis_id"]

    get_resp = await client.get(f"/api/analysis/{analysis_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == analysis_id
    assert data["status"] in ["pending", "processing_ocr", "processing_compliance", "completed"]
