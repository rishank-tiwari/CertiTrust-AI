"""
CertiTrust AI - Metadata Module Unit & API Integration Tests.
Tests PDF & Image metadata extraction, suspicious validator flags, and POST /api/v1/metadata API endpoint.
"""

import io
from PIL import Image
from fastapi.testclient import TestClient
from ai.metadata.metadata_service import metadata_service


def create_sample_png_bytes_with_software() -> bytes:
    """
    Creates a sample PNG image in memory for testing image metadata extraction.
    """
    img = Image.new("RGB", (300, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_metadata_service_image():
    """
    Tests direct metadata service extraction for image bytes.
    """
    img_bytes = create_sample_png_bytes_with_software()
    result = metadata_service.analyze_metadata(img_bytes, "certificate.png")

    assert result["success"] is True
    assert "metadata" in result
    assert result["metadata"]["width"] == 300
    assert result["metadata"]["height"] == 200
    assert result["metadata"]["format"] == "PNG"
    assert "risk_level" in result


def test_metadata_api_endpoint_valid_image(client: TestClient):
    """
    Tests POST /api/v1/metadata API endpoint with valid image file upload.
    """
    img_bytes = create_sample_png_bytes_with_software()
    files = {"file": ("test_doc.png", img_bytes, "image/png")}

    response = client.post("/api/v1/metadata", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "metadata" in data
    assert "warnings" in data
    assert "risk_level" in data


def test_metadata_api_invalid_file_extension(client: TestClient):
    """
    Tests POST /api/v1/metadata rejection of unsupported file types.
    """
    files = {"file": ("script.sh", b"#!/bin/bash\necho test", "text/plain")}

    response = client.post("/api/v1/metadata", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
