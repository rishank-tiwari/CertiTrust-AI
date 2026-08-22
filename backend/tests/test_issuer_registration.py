"""
CertiTrust AI - Issuer Portal Registration Test Suite.
Verifies registration of canonical credentials, hashing, unique ID generation, and gating rules.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.registry_service import credential_registry
from tests.test_credential_gating import (
    create_btech_marksheet_bytes,
    create_12th_marksheet_bytes,
    create_resume_bytes,
    create_random_screenshot_bytes,
)


def test_issuer_registration_workflow():
    client = TestClient(app)

    # Reset registry database before running test
    credential_registry.clear()

    # 1. Register a valid B.Tech Marksheet
    print("\n---------------------------------------------")
    print("Test 1: Register Valid B.Tech Semester Marksheet")
    res1 = client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("btech_marksheet.png", create_btech_marksheet_bytes(), "image/png")}
    )
    assert res1.status_code == 201
    data1 = res1.json()
    print("success:", data1["success"])
    print("credential_id:", data1["credential_id"])
    print("credential_type:", data1["credential_type"])
    print("issuer:", data1["issuer"])
    print("student_name:", data1["student_name"])
    print("document_hash:", data1["document_hash"])
    print("status:", data1["status"])
    print("blockchain_status:", data1["blockchain_status"])

    assert data1["success"] is True
    assert data1["credential_type"] == "B.Tech Semester Marksheet"
    assert data1["issuer"] == "Parul University"
    assert data1["student_name"] == "RISHANK TIWARI"
    assert data1["status"] == "ACTIVE"
    assert data1["blockchain_status"] == "NOT_CONFIGURED"
    assert "CERT-2026-" in data1["credential_id"]

    # Verify storage in Registry Service
    stored_rec = credential_registry.get_by_id(data1["credential_id"])
    assert stored_rec is not None
    assert stored_rec["recipient"]["student_name"] == "RISHANK TIWARI"
    assert stored_rec["recipient"]["student_identifier"] == "AF21650"
    assert stored_rec["credential_data"]["cgpa"] == 6.76

    # 2. Register a valid 12th Marksheet
    print("\n---------------------------------------------")
    print("Test 2: Register Valid 12th Marksheet")
    res2 = client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("marksheet_12th.png", create_12th_marksheet_bytes(), "image/png")}
    )
    assert res2.status_code == 201
    data2 = res2.json()
    print("success:", data2["success"])
    print("credential_id:", data2["credential_id"])
    print("credential_type:", data2["credential_type"])
    print("student_name:", data2["student_name"])

    assert data2["success"] is True
    assert data2["credential_type"] == "12th Marksheet"

    # 3. Try to register a Resume/CV (Gated -> Reject)
    print("\n---------------------------------------------")
    print("Test 3: Reject CV / Resume registration")
    res3 = client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("resume.png", create_resume_bytes(), "image/png")}
    )
    assert res3.status_code == 400
    data3 = res3.json()
    print("Response Status Code:", res3.status_code)
    print("Response detail:", data3["detail"])
    assert "not a supported educational credential" in data3["detail"].lower()

    # 4. Try to register a Random Screenshot (Gated -> Reject)
    print("\n---------------------------------------------")
    print("Test 4: Reject Random Screenshot registration")
    res4 = client.post(
        "/api/v1/issuer/credentials",
        files={"certificate": ("screenshot.png", create_random_screenshot_bytes(), "image/png")}
    )
    assert res4.status_code == 400
    data4 = res4.json()
    print("Response Status Code:", res4.status_code)
    print("Response detail:", data4["detail"])
    assert "not a supported educational credential" in data4["detail"].lower()

    print("\nALL ISSUER REGISTRATION PORTAL TESTS VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    test_issuer_registration_workflow()
