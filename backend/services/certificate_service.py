import os
import uuid
import shutil
from fastapi import UploadFile
from bson import ObjectId

async def save_uploaded_file(file: UploadFile, upload_dir: str) -> str:
    """Save uploaded file to disk with unique name, return file path."""
    os.makedirs(upload_dir, exist_ok=True)
    
    _, ext = os.path.splitext(file.filename)
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return file_path

async def create_certificate_record(db, certificate_data: dict) -> str:
    """Insert into certificates collection, return inserted ID as string."""
    result = await db.certificates.insert_one(certificate_data)
    return str(result.inserted_id)

async def get_certificate_by_id(db, certificate_id: str) -> dict | None:
    """Find certificate by ID."""
    if not ObjectId.is_valid(certificate_id):
        return None
    cert = await db.certificates.find_one({"_id": ObjectId(certificate_id)})
    if cert:
        cert["_id"] = str(cert["_id"])
    return cert

async def update_certificate_status(db, certificate_id: str, status: str) -> bool:
    """Update status field."""
    if not ObjectId.is_valid(certificate_id):
        return False
    result = await db.certificates.update_one(
        {"_id": ObjectId(certificate_id)},
        {"$set": {"status": status}}
    )
    return result.modified_count > 0

async def save_verification_result(db, verification_data: dict) -> str:
    """Insert into verifications collection."""
    result = await db.verifications.insert_one(verification_data)
    return str(result.inserted_id)

async def get_verification_by_certificate_id(db, certificate_id: str) -> dict | None:
    """Find verification by certificate_id."""
    verification = await db.verifications.find_one({"certificate_id": certificate_id})
    if verification:
        verification["_id"] = str(verification["_id"])
    return verification
