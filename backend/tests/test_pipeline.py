"""
CertiTrust AI - Comprehensive Pipeline & Integration Unit Tests.
Tests image preprocessing, OCR engine, entity extractor, fraud detector, trust scoring engine,
and FastAPI endpoint integration end-to-end.
"""

import io
from fastapi.testclient import TestClient
from ai.pipeline import pipeline


def test_ai_pipeline_direct_execution():
    """
    Tests direct 8-stage execution of the master AI pipeline.
    """
    sample_text_cert = (
        "CERTIFICATE OF ACHIEVEMENT\n"
        "Certificate ID: CERT-883920\n"
        "This is to certify that JANE DOE has completed Artificial Intelligence Masterclass.\n"
        "Issued by: DeepMind Academy\n"
        "Issue Date: 2026-05-10"
    )
    sample_bytes = sample_text_cert.encode("utf-8")

    result = pipeline.process_document("doc_test_123", "sample_certificate.txt", sample_bytes)

    assert result["document_id"] == "doc_test_123"
    assert "verdict" in result
    assert "trust_score" in result["verdict"]
    assert result["verdict"]["trust_score"] >= 0.0
    assert "blockchain_ready_payload" in result
    assert result["extracted_certificate_details"]["certificate_id"] is not None


def test_full_api_upload_and_verification_flow(client: TestClient):
    """
    Tests complete HTTP flow:
    1. POST /api/v1/documents/upload
    2. GET /api/v1/verification/{doc_id}
    3. GET /api/v1/blockchain/payload/{doc_id}
    4. POST /api/v1/verification/verify-hash
    """
    sample_content = b"CERTIFICATE OF COMPLETION\nIssued by Google DeepMind\nRecipient: Jane Doe\nID: CERT-998811"
    files = {"file": ("test_cert.txt", sample_content, "text/plain")}

    # 1. Upload File
    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    upload_data = upload_res.json()

    doc_id = upload_data["document_id"]
    sha256_hash = upload_data["sha256_hash"]

    assert doc_id.startswith("doc_")
    assert len(sha256_hash) == 64
    assert upload_data["status"] == "VERIFIED"

    # 2. Get Audit Report by Document ID
    report_res = client.get(f"/api/v1/verification/{doc_id}")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["document_id"] == doc_id
    assert "verdict" in report_data

    # 3. Get Blockchain Smart Contract Payload
    bc_res = client.get(f"/api/v1/blockchain/payload/{doc_id}")
    assert bc_res.status_code == 200
    bc_data = bc_res.json()
    assert bc_data["doc_hash"] == sha256_hash
    assert isinstance(bc_data["trust_score_scaled"], int)

    # 4. Verify by Cryptographic Hash
    hash_res = client.post("/api/v1/verification/verify-hash", json={"sha256_hash": sha256_hash})
    assert hash_res.status_code == 200
    assert hash_res.json()["document_id"] == doc_id
