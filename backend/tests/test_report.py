"""
CertiTrust AI - Explainable AI Report Generator Unit & Integration Tests.
Tests internal report generation, plain text rendering, and POST /api/v1/report API endpoint.
"""

from fastapi.testclient import TestClient
from ai.report.report_service import report_service


def test_report_service_direct_with_extracted_name():
    """
    Tests direct execution of ReportGeneratorService with real extracted student name.
    """
    input_data = {
        "authenticity_score": 94,
        "trust_score": 92,
        "forgery_risk": "Low",
        "decision": "Verified",
        "score_breakdown": {
            "ocr": 14,
            "information_extraction": 20,
            "metadata": 15,
            "computer_vision": 32,
            "validation": 14,
        },
        "student_name": "Alex Mercer",
        "university": "Massachusetts Institute of Technology",
        "certificate_number": "REG-44321",
        "issue_date": "2026-05-10",
    }

    result = report_service.generate_report(request_data=input_data)

    assert result["success"] is True
    assert "report_json" in result
    assert "report_text" in result

    report_json = result["report_json"]
    assert report_json["certificate_status"] == "Verified"
    assert report_json["authenticity_score"] == 94
    assert report_json["trust_score"] == 92
    assert report_json["extracted_information"]["student_name"] == "Alex Mercer"

    report_text = result["report_text"]
    assert "CERTITRUST AI VERIFICATION REPORT" in report_text
    assert "Verified" in report_text
    assert "Alex Mercer" in report_text


def test_report_service_missing_fields_displays_not_found():
    """
    Tests that missing fields display 'Not Found' instead of fake demo values.
    """
    input_data = {
        "authenticity_score": 50,
        "trust_score": 50,
        "forgery_risk": "Medium",
        "decision": "Needs Manual Review",
        "score_breakdown": {"ocr": 0, "information_extraction": 0, "metadata": 15, "computer_vision": 25, "validation": 10},
    }

    result = report_service.generate_report(request_data=input_data)

    assert result["success"] is True
    report_json = result["report_json"]
    assert report_json["extracted_information"]["student_name"] == "Not Found"
    assert report_json["extracted_information"]["university"] == "Not Found"
    assert report_json["extracted_information"]["certificate_number"] == "Not Found"


def test_report_api_endpoint(client: TestClient):
    """
    Tests POST /api/v1/report API endpoint.
    """
    payload = {
        "authenticity_score": 94,
        "trust_score": 92,
        "forgery_risk": "Low",
        "decision": "Verified",
        "score_breakdown": {
            "ocr": 14,
            "information_extraction": 20,
            "metadata": 15,
            "computer_vision": 32,
            "validation": 14,
        },
        "student_name": "Alex Mercer",
        "university": "Massachusetts Institute of Technology",
        "certificate_number": "REG-44321",
        "issue_date": "2026-05-10",
    }

    response = client.post("/api/v1/report", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "report_json" in data
    assert "report_text" in data
    assert data["report_json"]["extracted_information"]["student_name"] == "Alex Mercer"
    assert "Alex Mercer" in data["report_text"]
