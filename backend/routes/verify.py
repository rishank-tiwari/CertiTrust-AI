from fastapi import APIRouter, Depends, HTTPException
from database import get_database
from bson import ObjectId
from middleware.auth_middleware import require_role
from utils.api_payloads import build_verification_payload

router = APIRouter(tags=["Verification"])

@router.get("/verify/{certificate_id}")
async def verify_certificate(
    certificate_id: str,
    current_user: dict = Depends(require_role("employer")),
):
    db = get_database()
    cert_id = certificate_id
    try:
        cert_id = ObjectId(certificate_id)
    except Exception:
        pass
        
    cert = await db.credentials.find_one({"_id": cert_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.get("status") == "pending":
        return build_verification_payload(
            cert,
            None,
            fallback_certificate_id=certificate_id,
            verified_by=current_user.get("email"),
            status="pending",
        )

    verification = await db.verification_records.find_one({"certificate_id": certificate_id})
    return build_verification_payload(
        cert,
        verification,
        fallback_certificate_id=certificate_id,
        verified_by=current_user.get("email"),
    )
