"""
CertiTrust AI - Rule Validation Engine Unit & Integration Tests.
Tests individual rule functions, RuleValidationService execution, and POST /api/v1/validate API endpoint.
"""

from fastapi.testclient import TestClient
from ai.validation.validation_service import rule_validation_service


def get_mock_ai_outputs():
    """
    Returns realistic mock outputs from OCR, Extraction, Metadata, and Computer Vision modules.
    """
    ocr_data = {
        "success": True,
        "pages": [{"page": 1, "text": "This is to certify that Jane Doe has completed Bachelor of Technology at Stanford University. Cert ID: CT-998241 Issued on: 2026-05-10"}]
    }
    extraction_data = {
        "student_name": "Jane Doe",
        "university": "Stanford University",
        "degree": "Bachelor of Technology",
        "course": "Computer Science",
        "certificate_number": "CT-998241",
        "issue_date": "2026-05-10",
        "organization": "Stanford University",
        "cgpa": "3.85",
        "skills": ["Python"]
    }
    metadata_data = {
        "success": True,
        "metadata": {"creator": "LaTeX", "encrypted": False},
        "warnings": [],
        "risk_level": "Low"
    }
    cv_data = {
        "success": True,
        "logo_score": 95,
        "signature_score": 90,
        "stamp_score": 92,
        "layout_score": 94,
        "tampering_score": 5,
        "tampering_detected": False,
        "overall_cv_score": 94
    }
    return ocr_data, extraction_data, metadata_data, cv_data


def test_rule_validation_service_direct():
    """
    Tests direct execution of RuleValidationService.
    """
    ocr_data, extraction_data, metadata_data, cv_data = get_mock_ai_outputs()

    result = rule_validation_service.validate_credential(
        ocr_data=ocr_data,
        extraction_data=extraction_data,
        metadata_data=metadata_data,
        cv_data=cv_data,
    )

    assert result["success"] is True
    assert result["passed_rules"] == 10
    assert result["failed_rules"] == 0
    assert result["validation_score"] == 100
    assert len(result["validation_results"]) == 10


def test_validate_api_endpoint(client: TestClient):
    """
    Tests POST /api/v1/validate API endpoint.
    """
    ocr_data, extraction_data, metadata_data, cv_data = get_mock_ai_outputs()

    payload = {
        "ocr_data": ocr_data,
        "extraction_data": extraction_data,
        "metadata_data": metadata_data,
        "cv_data": cv_data,
        "logo_threshold": 70,
        "signature_threshold": 70,
        "layout_threshold": 70,
    }

    response = client.post("/api/v1/validate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "validation_results" in data
    assert "passed_rules" in data
    assert "failed_rules" in data
    assert "validation_score" in data
    assert data["validation_score"] == 100
