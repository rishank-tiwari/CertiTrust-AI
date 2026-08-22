"""
CertiTrust AI - Unified AI Pipeline Orchestrator Unit & Integration Tests.
Tests PipelineAnalysisService full 7-step execution sequence, timing metrics, and POST /api/v1/analyze API endpoint.
"""

import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from ai.pipeline.analysis_service import pipeline_analysis_service


def create_sample_cert_image() -> bytes:
    cert = Image.new("RGB", (600, 400), color=(245, 245, 245))
    logo = Image.new("RGB", (100, 100), color=(255, 255, 255))
    draw_logo = ImageDraw.Draw(logo)
    draw_logo.ellipse([20, 20, 80, 80], fill=(255, 0, 0), outline=(0, 0, 0))

    cert.paste(logo, (50, 50))
    draw_cert = ImageDraw.Draw(cert)
    draw_cert.text((160, 60), "Stanford University Certificate of Completion Jane Doe CT-998241 2026-05-10", fill=(0, 0, 0))
    draw_cert.ellipse([450, 250, 550, 350], fill=(200, 0, 0), outline=(100, 0, 0))
    draw_cert.line([(200, 320), (250, 310), (300, 330), (350, 315)], fill=(0, 0, 150), width=4)

    buf = io.BytesIO()
    cert.save(buf, format="PNG")
    return buf.getvalue()


def test_pipeline_analysis_service_direct():
    """
    Tests direct 7-step execution of PipelineAnalysisService.
    """
    cert_bytes = create_sample_cert_image()

    result = pipeline_analysis_service.run_full_pipeline(
        cert_bytes=cert_bytes,
        cert_filename="certificate.png",
    )

    assert result["success"] is True
    assert "execution_time_seconds" in result
    assert result["execution_time_seconds"] > 0
    assert "ocr" in result
    assert "information_extraction" in result
    assert "metadata" in result
    assert "computer_vision" in result
    assert "validation" in result
    assert "trust_score" in result
    assert "report" in result


def test_analyze_api_endpoint(client: TestClient):
    """
    Tests POST /api/v1/analyze API endpoint.
    """
    cert_bytes = create_sample_cert_image()
    files = {"certificate": ("certificate.png", cert_bytes, "image/png")}

    response = client.post("/api/v1/analyze", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "execution_time_seconds" in data
    assert "ocr" in data
    assert "information_extraction" in data
    assert "metadata" in data
    assert "computer_vision" in data
    assert "validation" in data
    assert "trust_score" in data
    assert "report" in data
