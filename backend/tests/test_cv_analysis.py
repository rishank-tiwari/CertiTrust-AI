"""
CertiTrust AI - Integrated Computer Vision Analysis Unit & Integration Tests.
Tests Logo, Signature, Stamp, Layout SSIM, and Tampering detection routines,
as well as the POST /api/v1/cv-analysis API endpoint.
"""

import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from ai.cv_analysis.cv_analysis_service import cv_analysis_service


def create_test_logo() -> bytes:
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, 80, 80], fill=(255, 0, 0), outline=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_test_certificate() -> bytes:
    cert = Image.new("RGB", (600, 400), color=(245, 245, 245))
    logo = Image.new("RGB", (100, 100), color=(255, 255, 255))
    draw_logo = ImageDraw.Draw(logo)
    draw_logo.ellipse([20, 20, 80, 80], fill=(255, 0, 0), outline=(0, 0, 0))

    cert.paste(logo, (50, 50))

    draw_cert = ImageDraw.Draw(cert)
    # Draw seal stamp
    draw_cert.ellipse([450, 250, 550, 350], fill=(200, 0, 0), outline=(100, 0, 0))
    # Draw signature stroke
    draw_cert.line([(200, 320), (250, 310), (300, 330), (350, 315)], fill=(0, 0, 150), width=4)

    buf = io.BytesIO()
    cert.save(buf, format="PNG")
    return buf.getvalue()


def test_integrated_cv_service_direct():
    """
    Tests direct execution of IntegratedCVAnalysisService.
    """
    cert_bytes = create_test_certificate()
    ref_template = cert_bytes
    ref_logo = create_test_logo()

    result = cv_analysis_service.analyze_certificate_vision(
        cert_bytes=cert_bytes,
        cert_filename="cert.png",
        ref_template_bytes=ref_template,
        ref_template_filename="template.png",
        ref_logo_bytes=ref_logo,
        ref_logo_filename="logo.png",
    )

    assert result["success"] is True
    assert 0 <= result["logo_score"] <= 100
    assert 0 <= result["signature_score"] <= 100
    assert 0 <= result["stamp_score"] <= 100
    assert 0 <= result["layout_score"] <= 100
    assert 0 <= result["tampering_score"] <= 100
    assert isinstance(result["tampering_detected"], bool)
    assert 0 <= result["overall_cv_score"] <= 100


def test_cv_analysis_api_endpoint(client: TestClient):
    """
    Tests POST /api/v1/cv-analysis API endpoint with 3 multipart file uploads.
    """
    cert_bytes = create_test_certificate()
    logo_bytes = create_test_logo()

    files = {
        "certificate": ("cert.png", cert_bytes, "image/png"),
        "reference_template": ("template.png", cert_bytes, "image/png"),
        "reference_logo": ("logo.png", logo_bytes, "image/png"),
    }

    response = client.post("/api/v1/cv-analysis", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "logo_score" in data
    assert "signature_score" in data
    assert "stamp_score" in data
    assert "layout_score" in data
    assert "tampering_score" in data
    assert "tampering_detected" in data
    assert "overall_cv_score" in data
