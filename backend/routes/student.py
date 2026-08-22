from fastapi import APIRouter, Depends, HTTPException
from middleware.auth_middleware import require_role
from database import get_database
from bson import ObjectId

router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/credentials")
async def get_student_credentials(
    current_user: dict = Depends(require_role("student"))
):
    """Get all credentials belonging to the authenticated student."""
    db = get_database()
    student_id = str(current_user["_id"])
    student_email = current_user.get("email", "")
    student_name = current_user.get("full_name", "")

    # Find credentials where the student is the recipient
    # Institutions upload credentials and set student_name/student_email
    query = {}
    if student_name:
        query["student_name"] = {"$regex": student_name, "$options": "i"}

    credentials = await db.credentials.find(query).sort("created_at", -1).limit(50).to_list(length=50)

    result = []
    for cert in credentials:
        cert_id = str(cert.pop("_id"))
        # Fetch verification data if exists
        verification = await db.verification_records.find_one({"certificate_id": cert_id})
        if verification:
            verification.pop("_id", None)
            if "verified_at" in verification and hasattr(verification["verified_at"], "isoformat"):
                verification["verified_at"] = verification["verified_at"].isoformat()

        if "created_at" in cert and hasattr(cert["created_at"], "isoformat"):
            cert["created_at"] = cert["created_at"].isoformat()

        result.append({
            "id": cert_id,
            **{k: v for k, v in cert.items()},
            "verification": verification
        })

    return {
        "credentials": result,
        "total": len(result),
        "student": {
            "name": student_name,
            "email": student_email,
            "role": current_user.get("role")
        }
    }


@router.get("/passport")
async def get_student_passport(
    current_user: dict = Depends(require_role("student"))
):
    """
    Get the authenticated student's full credential passport.
    Returns aggregated verified credentials and skill profile.
    """
    db = get_database()
    student_name = current_user.get("full_name", "")
    student_email = current_user.get("email", "")

    # Find all verified credentials for this student
    query = {}
    if student_name:
        query["student_name"] = {"$regex": student_name, "$options": "i"}

    all_certs = await db.credentials.find(query).sort("created_at", -1).to_list(length=100)

    verified_certs = []
    pending_certs = []

    for cert in all_certs:
        cert_id = str(cert.pop("_id"))
        if "created_at" in cert and hasattr(cert["created_at"], "isoformat"):
            cert["created_at"] = cert["created_at"].isoformat()

        verification = await db.verification_records.find_one({"certificate_id": cert_id})
        if verification:
            verification.pop("_id", None)
            if "verified_at" in verification and hasattr(verification["verified_at"], "isoformat"):
                verification["verified_at"] = verification["verified_at"].isoformat()

        cert_data = {"id": cert_id, **cert, "verification": verification}

        if cert.get("status") == "verified":
            verified_certs.append(cert_data)
        else:
            pending_certs.append(cert_data)

    # Calculate trust score based on verified credentials
    trust_score = min(100, len(verified_certs) * 15 + 10) if verified_certs else 0

    return {
        "student": {
            "name": student_name,
            "email": student_email,
            "id": str(current_user["_id"]),
            "organization": current_user.get("organization", ""),
        },
        "verified_credentials": verified_certs,
        "pending_credentials": pending_certs,
        "total_verified": len(verified_certs),
        "total_pending": len(pending_certs),
        "trust_score": trust_score,
    }
