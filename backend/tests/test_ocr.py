"""
CertiTrust AI - OCR Module Unit & API Integration Tests.
Tests image & PDF processing, OpenCV preprocessing, and POST /api/v1/upload endpoint.
"""

import io
from PIL import Image
from fastapi.testclient import TestClient
from ai.ocr.ocr_service import ocr_service


def create_sample_png_bytes() -> bytes:
    """
    Creates a valid PNG image in memory for testing image OCR uploading.
    """
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_ocr_service_direct_text_file():
    """
    Tests direct execution of OCR service on text/certificate file payload.
    """
    sample_content = b"Bachelor of Technology in Computer Science\nIssued by University of AI"
    result = ocr_service.process_document(sample_content, "degree_certificate.txt")

    assert result["success"] is True
    assert len(result["pages"]) == 1
    assert result["pages"][0]["page"] == 1
    assert "Bachelor of Technology" in result["pages"][0]["text"]


def test_upload_endpoint_valid_image(client: TestClient):
    """
    Tests POST /api/v1/upload with valid PNG image file upload.
    """
    sample_png = create_sample_png_bytes()
    files = {"file": ("test_certificate.png", sample_png, "image/png")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "pages" in data
    assert len(data["pages"]) >= 1
    assert data["pages"][0]["page"] == 1


def test_upload_endpoint_invalid_extension(client: TestClient):
    """
    Tests POST /api/v1/upload rejection of unsupported file extensions (e.g. .exe).
    """
    files = {"file": ("unsupported_script.exe", b"binary_data", "application/octet-stream")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
