from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth_middleware import require_role
from database import get_database
from models.certificate import AnalyzeRequest
from services import ai_service, blockchain_service
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter(tags=["Analysis"])


@router.post("/analyze")
async def analyze(
    request: AnalyzeRequest,
    current_user: dict = Depends(require_role("institution"))
):
    """
    Run AI analysis + blockchain storage on an uploaded certificate.
    This is the core pipeline endpoint.
    """
    db = get_database()

    cert_id = request.certificate_id
    try:
        cert_id = ObjectId(request.certificate_id)
    except Exception:
        pass

    # Fetch certificate
    cert = await db.credentials.find_one({"_id": cert_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Certificate is already '{cert.get('status')}', not pending")

    # Update status to analyzing
    await db.credentials.update_one({"_id": cert_id}, {"$set": {"status": "analyzing"}})

    # Step 1: AI Analysis (OCR + Fraud Detection)
    ai_result = await ai_service.analyze_certificate(cert.get("file_path", ""))

    # Step 2: Store hash on Blockchain
    blockchain_result = await blockchain_service.store_on_blockchain(
        certificate_hash=cert["file_hash"],
        issuer=cert.get("university", "Unknown")
    )

    # Step 3: Determine final status based on authenticity score
    authenticity_score = ai_result.get("authenticity_score", 0)
    final_status = "verified" if authenticity_score > 50 else "flagged"

    # Step 4: Update certificate status
    await db.credentials.update_one({"_id": cert_id}, {"$set": {"status": final_status}})

    # Step 5: Save verification result
    ai_fraud_list = ai_result.get("fraud_flags", [])
    reasons = []
    for flag in ai_fraud_list:
        reasons.append({
            "field": "document_forensics",
            "original_value": "Genuine",
            "submitted_value": flag,
            "reason": f"Forensic anomaly: {flag}",
            "severity": "HIGH"
        })
    fraud_flags_doc = {
        "status": "FAIL" if reasons else "PASS",
        "reasons": reasons
    }

    verification_doc = {
        "certificate_id": str(cert_id),
        "authenticity_score": authenticity_score,
        "risk_level": ai_result.get("risk_level", "high"),
        "fraud_flags": fraud_flags_doc,
        "extracted_data": ai_result.get("extracted_data", {}),
        "certificate_hash": cert["file_hash"],
        "blockchain_tx_hash": blockchain_result.get("tx_hash", ""),
        "blockchain_proof": blockchain_result,
        "status": final_status,
        "verified_at": datetime.now(timezone.utc)
    }

    result = await db.verification_records.insert_one(verification_doc)
    verification_doc["id"] = str(result.inserted_id)

    return {
        "message": f"Certificate analysis complete — {final_status}",
        "certificate_id": str(cert_id),
        "verification": {
            "id": verification_doc["id"],
            "authenticity_score": authenticity_score,
            "risk_level": ai_result.get("risk_level"),
            "fraud_flags": fraud_flags_doc,
            "extracted_data": ai_result.get("extracted_data", {}),
            "status": final_status
        },
        "blockchain": blockchain_result
    }
