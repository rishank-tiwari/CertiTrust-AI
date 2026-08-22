from datetime import datetime, timezone
import hashlib
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from database import get_database
from middleware.auth_middleware import require_role

router = APIRouter(prefix="/institution", tags=["Institution"])


def _certificate_payload(document: dict):
    return {
        "id": str(document.get("_id")) if document.get("_id") else document.get("id"),
        "student_name": document.get("student_name"),
        "student_email": document.get("student_email"),
        "university": document.get("university"),
        "degree": document.get("degree"),
        "course": document.get("course"),
        "certificate_number": document.get("certificate_number"),
        "status": document.get("status"),
        "created_at": document.get("created_at").isoformat() if document.get("created_at") else None,
    }


@router.post("/certificates")
async def create_certificate(
    student_name: str = Form(...),
    student_email: str = Form(""),
    university: str = Form(...),
    degree: str = Form(...),
    course: str = Form(""),
    certificate_number: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("institution")),
):
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".webp"]
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type '{file_ext}' not allowed.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    os.makedirs("uploads", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join("uploads", f"{timestamp}_{file.filename}")
    with open(path, "wb") as handle:
        handle.write(content)

    document = {
        "student_name": student_name,
        "student_email": student_email,
        "university": university,
        "degree": degree,
        "course": course,
        "certificate_number": certificate_number,
        "file_path": path,
        "file_hash": hashlib.sha256(content).hexdigest(),
        "status": "pending",
        "uploaded_by": str(current_user["_id"]),
        "created_at": datetime.now(timezone.utc),
    }

    db = get_database()
    result = await db.credentials.insert_one(document)
    document["_id"] = result.inserted_id
    return _certificate_payload(document)


@router.post("/certificates/bulk")
async def bulk_create_certificates(
    certificates: list[dict],
    current_user: dict = Depends(require_role("institution")),
):
    db = get_database()
    documents = []
    for item in certificates:
        documents.append(
            {
                "student_name": item.get("student_name"),
                "student_email": item.get("student_email", ""),
                "university": item.get("university"),
                "degree": item.get("degree"),
                "course": item.get("course", ""),
                "certificate_number": item.get("certificate_number"),
                "status": "pending",
                "uploaded_by": str(current_user["_id"]),
                "created_at": datetime.now(timezone.utc),
            }
        )

    if not documents:
        raise HTTPException(status_code=400, detail="No certificates provided.")

    result = await db.credentials.insert_many(documents)
    return {
        "created": len(result.inserted_ids),
        "certificate_ids": [str(item) for item in result.inserted_ids],
    }


@router.get("/credentials")
async def get_institution_credentials(
    current_user: dict = Depends(require_role("institution"))
):
    db = get_database()
    institution_id = str(current_user["_id"])

    credentials = await db.credentials.find(
        {"uploaded_by": institution_id}
    ).sort("created_at", -1).limit(100).to_list(length=100)

    return {
        "credentials": [_certificate_payload(cert) for cert in credentials],
        "total": len(credentials),
        "institution": {
            "name": current_user.get("organization") or current_user.get("full_name"),
            "email": current_user.get("email"),
            "id": institution_id,
        },
    }


@router.get("/analytics")
async def get_institution_analytics(
    current_user: dict = Depends(require_role("institution"))
):
    db = get_database()
    institution_id = str(current_user["_id"])

    total_certs = await db.credentials.count_documents({"uploaded_by": institution_id})
    verified_certs = await db.credentials.count_documents({"uploaded_by": institution_id, "status": "verified"})
    pending_certs = await db.credentials.count_documents({"uploaded_by": institution_id, "status": "pending"})
    flagged_certs = await db.credentials.count_documents({"uploaded_by": institution_id, "status": "flagged"})
    analyzing_certs = await db.credentials.count_documents({"uploaded_by": institution_id, "status": "analyzing"})

    cert_ids_cursor = db.credentials.find({"uploaded_by": institution_id}, {"_id": 1})
    cert_ids = [str(c["_id"]) async for c in cert_ids_cursor]

    external_verifications = await db.verification_records.count_documents(
        {"certificate_id": {"$in": cert_ids}}
    ) if cert_ids else 0

    verification_rate = round((verified_certs / total_certs * 100), 1) if total_certs > 0 else 0

    return {
        "institution": {
            "name": current_user.get("organization") or current_user.get("full_name"),
            "email": current_user.get("email"),
        },
        "summary": {
            "total_credentials": total_certs,
            "verified": verified_certs,
            "pending": pending_certs,
            "flagged": flagged_certs,
            "analyzing": analyzing_certs,
            "ai_verification_rate": verification_rate,
            "external_verifications": external_verifications,
        },
    }
