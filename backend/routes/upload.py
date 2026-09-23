from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from middleware.auth_middleware import require_role
from database import get_database
from models.certificate import CertificateResponse
import os
import hashlib
from datetime import datetime, timezone

router = APIRouter(tags=["Certificates"])


@router.post("/upload", response_model=CertificateResponse)
async def upload_certificate(
    student_name: str = Form(...),
    university: str = Form(...),
    degree: str = Form(...),
    certificate_number: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("institution"))
):
    """Upload a certificate file (PDF/image) with metadata. Institution role required."""
    # Validate file type
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".webp"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed. Allowed: {allowed_extensions}")

    import tempfile
    upload_dir = os.path.join(tempfile.gettempdir(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # Save with unique name to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_hash = hashlib.sha256(content).hexdigest()

    db = get_database()
    cert_doc = {
        "student_name": student_name,
        "university": university,
        "degree": degree,
        "certificate_number": certificate_number,
        "file_path": file_path,
        "file_hash": file_hash,
        "status": "pending",
        "uploaded_by": str(current_user["_id"]),
        "created_at": datetime.now(timezone.utc)
    }

    result = await db.credentials.insert_one(cert_doc)
    cert_doc["id"] = str(result.inserted_id)

    return CertificateResponse(**cert_doc)
