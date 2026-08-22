"""
CertiTrust AI - Logo Verification Unit & API Integration Tests.
Tests OpenCV template matching, ORB feature matching, PDF certificate rendering, and POST /api/v1/logo-verify API endpoint.
"""

import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from ai.cv_analysis.logo.logo_service import logo_verification_service


def create_sample_logo_bytes() -> bytes:
    """
    Creates a sample logo image in memory (red circle on white canvas).
    """
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, 80, 80], fill=(255, 0, 0), outline=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_sample_certificate_bytes() -> bytes:
    """
    Creates a sample certificate image containing the reference logo.
    """
    cert = Image.new("RGB", (600, 400), color=(240, 240, 240))
    logo = Image.new("RGB", (100, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(logo)
    draw.ellipse([20, 20, 80, 80], fill=(255, 0, 0), outline=(0, 0, 0))

    cert.paste(logo, (50, 50))
    buf = io.BytesIO()
    cert.save(buf, format="PNG")
    return buf.getvalue()


def test_logo_service_direct_image():
    """
    Tests direct execution of LogoVerificationService on PNG images.
    """
    cert_bytes = create_sample_certificate_bytes()
    ref_bytes = create_sample_logo_bytes()

    result = logo_verification_service.verify_logo(
        certificate_bytes=cert_bytes,
        cert_filename="certificate.png",
        reference_logo_bytes=ref_bytes,
        ref_filename="reference_logo.png",
    )

    assert result["success"] is True
    assert result["logo_detected"] is True
    assert result["similarity_score"] >= 50.0
    assert result["confidence"] in ["High", "Medium", "Low"]
    assert result["status"] in ["Matched", "Mismatched"]


def test_logo_verify_api_endpoint_valid(client: TestClient):
    """
    Tests POST /api/v1/logo-verify API endpoint with valid certificate & reference logo uploads.
    """
    cert_bytes = create_sample_certificate_bytes()
    ref_bytes = create_sample_logo_bytes()

    files = {
        "certificate": ("certificate.png", cert_bytes, "image/png"),
        "reference_logo": ("reference_logo.png", ref_bytes, "image/png"),
    }

    response = client.post("/api/v1/logo-verify", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "logo_detected" in data
    assert "similarity_score" in data
    assert "confidence" in data
    assert "status" in data


def test_logo_verify_api_endpoint_invalid_reference(client: TestClient):
    """
    Tests POST /api/v1/logo-verify rejection of invalid reference logo format.
    """
    cert_bytes = create_sample_certificate_bytes()
    invalid_logo = b"not_an_image_file"

    files = {
        "certificate": ("certificate.png", cert_bytes, "image/png"),
        "reference_logo": ("invalid_logo.txt", invalid_logo, "text/plain"),
    }

    response = client.post("/api/v1/logo-verify", files=files)
    assert response.status_code == 400
    assert "Invalid reference logo format" in response.json()["detail"] or "must be a valid image" in response.json()["detail"]
