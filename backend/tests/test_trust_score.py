"""
CertiTrust AI - Trust Score Engine Unit & Integration Tests.
Tests TrustScoreService calculation, decision mapping, score breakdown, and POST /api/v1/trust-score API endpoint.
"""

from fastapi.testclient import TestClient
from ai.trust_score.trust_score_service import trust_score_service


def get_mock_ai_payloads():
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
    validation_data = {
        "success": True,
        "validation_results": [],
        "passed_rules": 10,
        "failed_rules": 0,
        "validation_score": 100
    }
    return ocr_data, extraction_data, metadata_data, cv_data, validation_data


def test_trust_score_service_direct():
    """
    Tests direct execution of TrustScoreService.
    """
    ocr, ext, meta, cv, val = get_mock_ai_payloads()

    result = trust_score_service.calculate_trust_score(
        ocr_data=ocr,
        extraction_data=ext,
        metadata_data=meta,
        cv_data=cv,
        validation_data=val,
    )

    assert result["success"] is True
    assert result["authenticity_score"] >= 90
    assert result["trust_score"] >= 90
    assert result["decision"] == "Verified"
    assert result["forgery_risk"] in ["Very Low", "Low"]
    assert "score_breakdown" in result
    assert result["score_breakdown"]["ocr"] == 15
    assert result["score_breakdown"]["information_extraction"] == 20
    assert result["score_breakdown"]["metadata"] == 15


def test_trust_score_api_endpoint(client: TestClient):
    """
    Tests POST /api/v1/trust-score API endpoint.
    """
    ocr, ext, meta, cv, val = get_mock_ai_payloads()

    payload = {
        "ocr_data": ocr,
        "extraction_data": ext,
        "metadata_data": meta,
        "cv_data": cv,
        "validation_data": val,
    }

    response = client.post("/api/v1/trust-score", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "authenticity_score" in data
    assert "trust_score" in data
    assert "forgery_risk" in data
    assert "decision" in data
    assert "score_breakdown" in data
    assert data["decision"] == "Verified"
