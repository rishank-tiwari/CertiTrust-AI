from datetime import datetime, timezone
import hashlib
import os
import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from database import get_database
from middleware.auth_middleware import require_role
from services import ai_service, blockchain_service
from utils.api_payloads import build_verification_payload

# Import AI resume parsing modules
from ai.ocr.ocr_service import ocr_service
from ai.resume_intelligence.resume_analysis_service import resume_analysis_service
from app.services.registry_service import credential_registry

router = APIRouter(prefix="/employer", tags=["Employer"])

ALLOWED_RESUME_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp", "docx", "txt"}

# Resume gating keywords
RESUME_POSITIVE_KEYWORDS = [
    "resume", "curriculum vitae", "cv", "objective", "career objective",
    "professional summary", "work experience", "technical skills",
    "projects", "about me", "professional experience", "key skills",
    "core competencies", "tools and technologies",
    "hackathon", "extracurricular",
]

CREDENTIAL_NEGATIVE_KEYWORDS = [
    "marksheet", "mark sheet", "statement of marks", "board of secondary",
    "examination result", "certificate of", "certify that", "awarded to",
    "this is to certify", "has successfully completed",
    "provisional degree", "degree certificate", "semester examination",
    "internship completion", "certificate of internship",
    "certificate of achievement", "training certificate",
]


def _save_upload(directory: str, file: UploadFile, content: bytes) -> str:
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    path = os.path.join(directory, safe_name)
    with open(path, "wb") as handle:
        handle.write(content)
    return path


def _normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def _classify_as_resume(text: str, filename: str) -> dict:
    """Helper to classify if document is a resume."""
    text_lower = text.lower()
    fname_lower = filename.lower()

    fname_is_resume = any(kw in fname_lower for kw in ["resume", "cv", "curriculum"])
    fname_is_credential = any(kw in fname_lower for kw in ["marksheet", "certificate", "degree", "transcript"])

    resume_score = 0
    credential_score = 0

    for kw in RESUME_POSITIVE_KEYWORDS:
        if kw in text_lower:
            resume_score += 1

    for kw in CREDENTIAL_NEGATIVE_KEYWORDS:
        if kw in text_lower:
            credential_score += 1

    if len(text.strip()) < 50:
        return {
            "is_resume": False,
            "document_type": "NOT_A_RESUME",
            "confidence": 0.95,
            "reason": "Document text is too short to be a resume.",
        }

    if fname_is_credential and credential_score > resume_score:
        return {
            "is_resume": False,
            "document_type": "NOT_A_RESUME",
            "confidence": 0.90,
            "reason": "Document appears to be a credential/certificate.",
        }

    if credential_score > 3 and resume_score <= 1:
        return {
            "is_resume": False,
            "document_type": "NOT_A_RESUME",
            "confidence": 0.85,
            "reason": "Document content strongly indicates a credential/certificate, not a resume.",
        }

    if resume_score >= 2 or fname_is_resume:
        return {
            "is_resume": True,
            "document_type": "RESUME",
            "confidence": min(0.95, 0.60 + resume_score * 0.05),
            "reason": f"Resume detected (resume signals: {resume_score}).",
        }

    return {
        "is_resume": False,
        "document_type": "NOT_A_RESUME",
        "confidence": 0.60,
        "reason": "Document does not contain sufficient resume indicators.",
    }


import re

def _normalize_value(val) -> str:
    if val is None:
        return ""
    val_str = str(val).strip().lower()
    val_str = re.sub(r'\s+', ' ', val_str)
    val_str = re.sub(r'[^a-z0-9\.\s\-]', '', val_str)
    return val_str.strip()


def _parse_numeric(val) -> float | None:
    if val is None:
        return None
    try:
        match = re.search(r'\d+(?:\.\d+)?', str(val))
        if match:
            return float(match.group(0))
    except Exception:
        pass
    return None


@router.post("/verify-certificate")
@router.post("/verify-credential")
async def employer_verify_certificate(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("employer")),
):
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".webp"]
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type '{file_ext}' not allowed.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")

    temp_path = _save_upload("./uploads/employer_temp", file, content)
    file_hash = hashlib.sha256(content).hexdigest()
    ai_result = await ai_service.analyze_certificate(temp_path)
    extracted_data = ai_result.get("extracted_data", {})

    db = get_database()
    certificate = None
    certificate_number = extracted_data.get("certificate_number")
    student_name = extracted_data.get("student_name")

    if certificate_number:
        certificate = await db.credentials.find_one({"certificate_number": certificate_number})
    if not certificate and student_name:
        certificate = await db.credentials.find_one(
            {"student_name": {"$regex": student_name, "$options": "i"}}
        )

    blockchain_result = await blockchain_service.store_on_blockchain(
        certificate_hash=file_hash,
        issuer=extracted_data.get("university") or "Employer Verification",
    )

    # Perform Source of Truth comparison logic
    hash_match = False
    field_comparison = {}
    changed_parameters_list = []
    fraud_reasons = []

    # Map validation/forensic flags from AI pipeline
    for f in ai_result.get("fraud_flags", []):
        fraud_reasons.append({
            "field": "document_forensics",
            "original_value": "Genuine",
            "submitted_value": f,
            "reason": f"Forensic anomaly: {f}",
            "severity": "HIGH"
        })

    message = ""

    if certificate:
        hash_match = (certificate.get("file_hash") == file_hash)
        
        # Compare key academic identity fields
        fields_to_compare = [
            ("student_name", "student_name", "student name", "CRITICAL"),
            ("degree", "degree", "degree", "CRITICAL"),
            ("university", "university", "university", "CRITICAL"),
            ("certificate_number", "certificate_number", "certificate number/roll number", "CRITICAL"),
            ("cgpa", "cgpa", "cgpa", "CRITICAL"),
            ("percentage", "percentage", "percentage", "CRITICAL")
        ]
        
        for issuer_key, submitted_key, field_label, severity in fields_to_compare:
            issuer_val = certificate.get(issuer_key)
            submitted_val = extracted_data.get(submitted_key)
            
            if issuer_val is not None and submitted_val is not None:
                norm_issuer = _normalize_value(issuer_val)
                norm_submitted = _normalize_value(submitted_val)
                
                if norm_issuer and norm_submitted:
                    match = False
                    if issuer_key in ["cgpa", "percentage"]:
                        num_issuer = _parse_numeric(issuer_val)
                        num_submitted = _parse_numeric(submitted_val)
                        if num_issuer is not None and num_submitted is not None:
                            match = (abs(num_issuer - num_submitted) < 0.01)
                            
                    if not match:
                        match = (norm_issuer == norm_submitted or norm_issuer in norm_submitted or norm_submitted in norm_issuer)
                        
                    field_comparison[issuer_key] = {
                        "submitted": str(submitted_val),
                        "stored": str(issuer_val),
                        "match": match
                    }
                    
                    if not match:
                        fraud_reasons.append({
                            "field": issuer_key,
                            "original_value": issuer_val,
                            "submitted_value": submitted_val,
                            "reason": f"Trusted issuer {field_label} value differs from submitted value",
                            "severity": severity
                        })
                        changed_parameters_list.append({
                            "field": issuer_key,
                            "original_value": issuer_val,
                            "submitted_value": submitted_val,
                            "status": "CHANGED",
                            "severity": severity
                        })
                        
        # Compare subjects & marks if present in issuer record
        issuer_subjects = certificate.get("subjects") or []
        submitted_subjects = extracted_data.get("subjects") or []
        if issuer_subjects:
            for isub in issuer_subjects:
                sub_name = isub.get("subject") or isub.get("name")
                norm_sub_name = _normalize_value(sub_name)
                
                matched_sub = None
                for ssub in submitted_subjects:
                    ssub_name = ssub.get("subject") or ssub.get("name")
                    if _normalize_value(ssub_name) == norm_sub_name:
                        matched_sub = ssub
                        break
                        
                if matched_sub:
                    i_marks = _parse_numeric(isub.get("marks_obtained") or isub.get("marks"))
                    s_marks = _parse_numeric(matched_sub.get("marks_obtained") or matched_sub.get("marks"))
                    
                    if i_marks is not None and s_marks is not None:
                        if abs(i_marks - s_marks) >= 0.01:
                            fraud_reasons.append({
                                "field": f"subject_{sub_name}_marks",
                                "original_value": i_marks,
                                "submitted_value": s_marks,
                                "reason": f"Marks obtained for subject '{sub_name}' differs from trusted issuer value",
                                "severity": "CRITICAL"
                            })
                            changed_parameters_list.append({
                                "field": f"subject_{sub_name}_marks",
                                "original_value": i_marks,
                                "submitted_value": s_marks,
                                "status": "CHANGED",
                                "severity": "CRITICAL"
                            })

        if fraud_reasons:
            verification_status = "flagged"
            risk_level = "high"
            fraud_status = "FAIL"
        else:
            verification_status = "verified"
            risk_level = "low"
            fraud_status = "PASS"
            if not hash_match:
                message = "File hash differs, but the credential content matches the issuer's trusted record."
    else:
        verification_status = "not_verified"
        risk_level = "high"
        fraud_status = "FAIL" if fraud_reasons else "PASS"

    fraud_flags_doc = {
        "status": fraud_status,
        "reasons": fraud_reasons
    }

    verification_doc = {
        "type": "employer_verification",
        "credential_id": str(certificate["_id"]) if certificate else None,
        "certificate_id": str(certificate["_id"]) if certificate else None,
        "employer_id": str(current_user["_id"]),
        "employer_email": current_user.get("email"),
        "original_filename": file.filename,
        "submitted_document_hash": file_hash,
        "hash_match": hash_match,
        "field_comparison": field_comparison,
        "changed_parameters": changed_parameters_list,
        "authenticity_score": ai_result.get("authenticity_score", 0),
        "risk_level": risk_level,
        "fraud_flags": fraud_flags_doc,
        "extracted_data": extracted_data,
        "certificate_hash": file_hash,
        "blockchain_tx_hash": blockchain_result.get("tx_hash"),
        "blockchain_proof": blockchain_result,
        "status": verification_status,
        "verification_status": verification_status,
        "verified_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "message": message
    }

    result = await db.verification_records.insert_one(verification_doc)
    verification_doc["id"] = str(result.inserted_id)

    payload = build_verification_payload(
        certificate,
        verification_doc,
        fallback_certificate_id=verification_doc["id"],
        verified_by=current_user.get("email"),
        status=verification_status,
    )
    if message:
        payload["message"] = message
        
    return payload


@router.post("/verify-resume")
async def employer_verify_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("employer")),
):
    file_ext = os.path.splitext(file.filename or "")[1].lower().replace(".", "")
    if file_ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{file_ext}'."
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")

    # 1. Save and run OCR/docx extraction
    temp_path = _save_upload("./uploads/resume_temp", file, content)
    resume_hash = hashlib.sha256(content).hexdigest()

    extracted_text = ""
    if file_ext == "docx":
        extracted_text = _extract_text_from_docx(content)
    else:
        try:
            ocr_result = ocr_service.process_document(content, file.filename)
            if isinstance(ocr_result, dict):
                pages = ocr_result.get("pages", [])
                if isinstance(pages, list):
                    extracted_text = "\n".join(
                        str(p.get("text", "")) for p in pages if isinstance(p, dict)
                    )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from resume: {str(e)}"
            )

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract readable text from resume.")

    # 2. Gate check
    gate_result = _classify_as_resume(extracted_text, file.filename)
    if not gate_result["is_resume"]:
        raise HTTPException(status_code=400, detail=gate_result["reason"])

    db = get_database()

    # 3. Dynamic bridge: Query all certificates from MongoDB and load into credential_registry._db
    all_credentials = await db.credentials.find({}).to_list(length=1000)
    credential_registry._db = {
        str(c["_id"]): {
            "credential_id": str(c["_id"]),
            "credential_type": f"{c.get('degree', '')} {c.get('course', '')}",
            "credential_data": c
        }
        for c in all_credentials
    }

    # 4. Perform Resume Analysis (OCR + NLP + Skill Passport + Github Analysis)
    analysis = resume_analysis_service.analyze_resume(extracted_text)

    # 5. Store resume_analysis results in MongoDB
    resume_analysis_doc = {
        "resume_hash": resume_hash,
        "candidate_information": analysis.get("candidate"),
        "extracted_skills": analysis.get("skills"),
        "skill_passport_results": analysis.get("skill_verification"),
        "project_analysis": analysis.get("project_analysis"),
        "github_analysis": analysis.get("github_analysis"),
        "credibility_score": analysis.get("resume_analysis", {}).get("overall_score", 0),
        "risk_analysis": analysis.get("risk"),
        "ai_summary": analysis.get("full_summary"),
        "created_at": datetime.now(timezone.utc)
    }
    await db.resume_analysis.insert_one(resume_analysis_doc)

    # 6. Retrieve student from DB
    extracted_email = analysis.get("candidate", {}).get("email")
    extracted_name = analysis.get("candidate", {}).get("name")
    student = None
    if extracted_email:
        student = await db.users.find_one({"email": extracted_email, "role": "student"})
    if not student and extracted_name:
        student = await db.users.find_one(
            {"full_name": {"$regex": extracted_name, "$options": "i"}, "role": "student"}
        )

    # 7. Map skill verification status
    skill_results = []
    for s in analysis.get("skill_verification", []):
        skill_results.append({
            "skill": s["skill"],
            "status": "verified" if s["verification_status"] == "VERIFIED" else "not_verified"
        })

    # 8. Store verification record in MongoDB
    verification_doc = {
        "type": "resume_verification",
        "employer_id": str(current_user["_id"]),
        "employer_email": current_user.get("email"),
        "original_filename": file.filename,
        "resume_hash": resume_hash,
        "status": "completed",
        "verified_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "student_id": str(student["_id"]) if student else None,
        "skill_results": skill_results
    }
    result = await db.verification_records.insert_one(verification_doc)

    return {
        "verification_id": str(result.inserted_id),
        "status": "completed",
        "matched_student": {
            "id": str(student["_id"]),
            "name": student.get("full_name"),
            "email": student.get("email"),
        } if student else None,
        "skill_results": skill_results,
    }


@router.get("/verification-history")
@router.get("/history")
async def get_verification_history(
    current_user: dict = Depends(require_role("employer")),
):
    db = get_database()
    employer_id = str(current_user["_id"])
    records = await db.verification_records.find({"employer_id": employer_id}).sort(
        "verified_at", -1
    ).limit(50).to_list(length=50)

    history = []
    for record in records:
        history.append(
            {
                "id": str(record.get("_id")),
                "type": record.get("type"),
                "status": record.get("status"),
                "filename": record.get("original_filename"),
                "verified_at": record.get("verified_at").isoformat() if record.get("verified_at") else None,
                "certificate_id": record.get("certificate_id"),
            }
        )

    return {"history": history, "total": len(history)}
