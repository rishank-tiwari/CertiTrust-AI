"""
CertiTrust AI - Issuer Portal Endpoint Router.
Provides POST /api/v1/issuer/credentials endpoint to register original trusted canonical credentials.
"""

import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.pipeline.analysis_service import pipeline_analysis_service
from app.services.registry_service import credential_registry
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/issuer", tags=["Issuer Portal Management"])

ALLOWED_DOC_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}


@router.post(
    "/credentials",
    status_code=status.HTTP_201_CREATED,
    summary="Register Original Credential as Source of Truth",
    description="Authorized issuer uploads original academic credential. Generates canonical record, SHA-256 hash, and CERT ID.",
)
async def register_issuer_credential(
    certificate: UploadFile = File(..., description="Uploaded Original Certificate/Marksheet File (PDF/PNG/JPG/JPEG)")
):
    """
    Ingests and validates original credential from an authorized issuer.
    Generates canonical representation, SHA-256 hash, stable unique ID, and logs to registry.
    """
    logger.info(f"Issuer registration request received for file: '{certificate.filename}'")

    if not certificate.filename or "." not in certificate.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded certificate must have a valid filename with an extension.",
        )

    cert_ext = certificate.filename.lower().split(".")[-1]
    if cert_ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{cert_ext}'. Allowed formats: {', '.join(ALLOWED_DOC_EXTENSIONS)}",
        )

    cert_bytes = await certificate.read()
    if len(cert_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(cert_bytes) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum permitted limit of {max_mb:.1f} MB.",
        )

    # 1. Run full pipeline to extract details
    try:
        pipeline_res = pipeline_analysis_service.run_full_pipeline(
            cert_bytes=cert_bytes,
            cert_filename=certificate.filename,
            ref_template_bytes=None,
            ref_template_filename=None,
            ref_logo_bytes=None,
            ref_logo_filename=None,
        )
    except Exception as e:
        logger.error(f"Error during AI pipeline extraction for issuer registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI pipeline analysis failed during issuer processing: {str(e)}",
        )

    # Gating Check: Must be a supported educational credential
    if not pipeline_res.get("is_supported", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register: The uploaded file is not a supported educational credential.",
        )

    # 2. Generate SHA-256 Hash of original file bytes
    doc_hash = hashlib.sha256(cert_bytes).hexdigest()

    # 3. Generate Unique, Stable Credential ID
    unique_suffix = doc_hash[:8].upper()
    credential_id = f"CERT-2026-{unique_suffix}"

    # 4. Construct Authorized Issuer Abstraction
    ext_data = pipeline_res.get("information_extraction") or {}
    doc_type = pipeline_res.get("document_type", "Academic Certificate")

    extracted_issuer = ext_data.get("university") or ext_data.get("board") or ext_data.get("organization") or "Unknown Issuer"
    if extracted_issuer == "Not Found" or not extracted_issuer:
        extracted_issuer = "Parul University"  # Default fallback for prototype matching

    issuer_info = {
        "issuer_id": f"PU-{unique_suffix[:4]}",
        "name": extracted_issuer,
        "issuer_type": "Board" if ("board" in str(extracted_issuer).lower() or "rbse" in str(extracted_issuer).lower()) else "University",
        "issuer_status": "AUTHORIZED"
    }

    # 5. Build Recipient Info
    student_name = ext_data.get("student_name") or "Unknown Student"
    student_id = ext_data.get("roll_number") or ext_data.get("registration_number") or "N/A"

    recipient_info = {
        "student_name": student_name,
        "student_identifier": student_id
    }

    # 6. Build Canonical Credential Data depending on type
    doc_type_clean = doc_type.lower()
    is_btech = "b.tech" in doc_type_clean or "btech" in doc_type_clean
    is_marksheet = "marksheet" in doc_type_clean or "board" in doc_type_clean or "transcript" in doc_type_clean

    if is_btech:
        credential_data = {
            "degree": ext_data.get("degree"),
            "program": ext_data.get("program"),
            "semester": ext_data.get("semester"),
            "semester_name": ext_data.get("semester_name"),
            "subjects": ext_data.get("subjects", []),
            "sgpa": ext_data.get("sgpa"),
            "cgpa": ext_data.get("cgpa"),
            "percentage": ext_data.get("percentage"),
            "result": ext_data.get("result"),
            "division": ext_data.get("division"),
        }
    elif is_marksheet:
        credential_data = {
            "board": ext_data.get("board"),
            "exam": ext_data.get("exam"),
            "exam_year": ext_data.get("exam_year"),
            "roll_number": ext_data.get("roll_number"),
            "subjects": ext_data.get("subjects", []),
            "total_max_marks": ext_data.get("total_max_marks"),
            "total_marks_obtained": ext_data.get("total_marks_obtained"),
            "percentage": ext_data.get("percentage"),
            "result": ext_data.get("result"),
        }
    else:
        credential_data = {
            "degree": ext_data.get("degree"),
            "course": ext_data.get("course"),
            "certificate_number": ext_data.get("certificate_number"),
            "cgpa": ext_data.get("cgpa"),
            "issue_date": ext_data.get("issue_date"),
        }

    # 7. Document metadata info
    issued_date = ext_data.get("dated") or ext_data.get("document_date") or ext_data.get("issue_date")

    document_info = {
        "original_filename": certificate.filename,
        "mime_type": certificate.content_type,
        "sha256": doc_hash,
        "issued_date": issued_date
    }

    # 8. Compile full record
    canonical_record = {
        "credential_id": credential_id,
        "credential_type": doc_type,
        "issuer": issuer_info,
        "recipient": recipient_info,
        "credential_data": credential_data,
        "document": document_info,
        "status": "ACTIVE",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    # Register record in Simulated Database Registry
    credential_registry.register(canonical_record)

    return {
        "success": True,
        "credential_id": credential_id,
        "credential_type": doc_type,
        "issuer": issuer_info["name"],
        "student_name": student_name,
        "document_hash": doc_hash,
        "status": "ACTIVE",
        "registered_at": canonical_record["created_at"],
        "message": "Credential successfully registered as a trusted issuer record.",
        "blockchain_status": "NOT_CONFIGURED"
    }
