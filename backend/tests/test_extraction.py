"""
CertiTrust AI - Information Extraction Unit & Integration Tests.
Tests extraction_service entity extraction logic and POST /api/v1/extract API endpoint.
"""

from fastapi.testclient import TestClient
from ai.extraction.extraction_service import extraction_service


def test_extraction_service_direct():
    """
    Tests direct extraction service on sample certificate text.
    """
    sample_text = (
        "CERTIFICATE OF COMPLETION\n"
        "This is to certify that Jane Doe\n"
        "has successfully completed Bachelor of Technology in Computer Science\n"
        "from Stanford University.\n"
        "Certificate ID: CT-998241\n"
        "Issue Date: 2026-05-10\n"
        "CGPA: 3.85/4.0\n"
        "Skills: Python, Machine Learning, FastApi"
    )

    result = extraction_service.extract_information(sample_text)

    assert result["student_name"] == "Jane Doe"
    assert result["university"] == "Stanford University"
    assert "Bachelor of Technology" in result["degree"]
    assert "Computer Science" in result["course"]
    assert result["certificate_number"] == "CT-998241"
    assert result["issue_date"] == "2026-05-10"
    assert result["cgpa"] == "3.85/4.0"
    assert "Python" in result["skills"]
    assert "Machine Learning" in result["skills"]


def test_extract_api_endpoint(client: TestClient):
    """
    Tests POST /api/v1/extract API endpoint response.
    """
    payload = {
        "text": (
            "This is to certify that Alex Mercer has completed Master of Science in Artificial Intelligence "
            "from Massachusetts Institute of Technology on 2025-11-20. Reg No: REG-44321. CGPA: 3.9"
        )
    }

    response = client.post("/api/v1/extract", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["student_name"] == "Alex Mercer"
    assert data["university"] == "Massachusetts Institute of Technology"
    assert data["degree"] == "Master of Science"
    assert data["course"] == "Artificial Intelligence"
    assert data["certificate_number"] == "REG-44321"
    assert data["issue_date"] == "2025-11-20"
    assert data["cgpa"] == "3.9"


def test_extract_api_empty_text(client: TestClient):
    """
    Tests POST /api/v1/extract validation for empty text payload.
    """
    response = client.post("/api/v1/extract", json={"text": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]
