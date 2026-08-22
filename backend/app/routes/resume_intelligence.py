"""
CertiTrust AI - Resume Intelligence Endpoint Router.
Provides POST /api/v1/employer/analyze-resume endpoint for complete resume
analysis, skill extraction, and Skill Passport verification.
Does NOT modify or interfere with the existing credential verification endpoint.
"""

import io
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.ocr.ocr_service import ocr_service
from ai.resume_intelligence.resume_analysis_service import resume_analysis_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/employer", tags=["Employer Portal - Resume Intelligence"])

ALLOWED_RESUME_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "docx"}

# Resume-positive and credential-negative keywords for resume gating
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


def classify_as_resume(text: str, filename: str) -> Dict[str, Any]:
    """
    Resume Gate: Determines if the uploaded document is actually a resume.
    Returns classification result with confidence.
    """
    text_lower = text.lower()
    fname_lower = filename.lower()

    # Filename-based detection
    fname_is_resume = any(kw in fname_lower for kw in ["resume", "cv", "curriculum"])
    fname_is_credential = any(kw in fname_lower for kw in ["marksheet", "certificate", "degree", "transcript"])

    # Content-based scoring
    resume_score = 0
    credential_score = 0

    for kw in RESUME_POSITIVE_KEYWORDS:
        if kw in text_lower:
            resume_score += 1

    for kw in CREDENTIAL_NEGATIVE_KEYWORDS:
        if kw in text_lower:
            credential_score += 1

    # Decision logic
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
            "reason": f"Document appears to be a credential/certificate (credential signals: {credential_score}, resume signals: {resume_score}).",
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

    if resume_score >= 1 and credential_score == 0:
        return {
            "is_resume": True,
            "document_type": "RESUME",
            "confidence": 0.65,
            "reason": "Likely a resume based on content analysis.",
        }

    # Default: not a resume
    return {
        "is_resume": False,
        "document_type": "NOT_A_RESUME",
        "confidence": 0.60,
        "reason": "Document does not contain sufficient resume indicators.",
    }


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from a DOCX file using python-docx.
    Falls back gracefully if python-docx is not installed.
    """
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except ImportError:
        logger.warning("python-docx not installed. DOCX text extraction unavailable.")
        return ""
    except Exception as e:
        logger.warning(f"DOCX extraction failed: {str(e)}")
        return ""


@router.post(
    "/analyze-resume",
    status_code=status.HTTP_200_OK,
    summary="Analyze Candidate Resume with Skill Passport Verification",
    description="Employer uploads a candidate's resume. CertiTrust AI extracts all information, "
                "builds a claim inventory, and verifies skills/education against the Skill Passport.",
)
@router.post(
    "/resume/analyze",
    status_code=status.HTTP_200_OK,
    summary="Analyze Candidate Resume (Preferred Endpoint)",
    description="Employer uploads a candidate's resume. CertiTrust AI extracts all information, "
                "builds a claim inventory, and verifies skills/education against the Skill Passport.",
)
async def analyze_resume(
    resume: UploadFile = File(..., description="Uploaded Candidate Resume (PDF/PNG/JPG/JPEG/DOCX)")
):
    """
    Resume Intelligence endpoint:
    1. Resume Gate - validates document is a resume
    2. OCR / Text extraction
    3. Full structured extraction
    4. Skill Passport verification
    5. Returns complete analysis
    """
    logger.info(f"Resume Intelligence: Request received for file: '{resume.filename}'")

    # Validate filename
    if not resume.filename or "." not in resume.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded resume must have a valid filename with an extension.",
        )

    file_ext = resume.filename.lower().split(".")[-1]
    if file_ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{file_ext}'. Allowed formats: {', '.join(ALLOWED_RESUME_EXTENSIONS)}",
        )

    # Read file bytes
    file_bytes = await resume.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    if len(file_bytes) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum permitted limit of {max_mb:.1f} MB.",
        )

    # Step 1: Extract text (OCR for images/PDFs, native for DOCX)
    logger.info(f"Resume Intelligence: Extracting text from '{resume.filename}'...")
    extracted_text = ""

    if file_ext == "docx":
        extracted_text = extract_text_from_docx(file_bytes)
    else:
        try:
            ocr_result = ocr_service.process_document(file_bytes, resume.filename)
            if isinstance(ocr_result, dict):
                pages = ocr_result.get("pages", [])
                if isinstance(pages, list):
                    extracted_text = "\n".join(
                        str(p.get("text", "")) for p in pages if isinstance(p, dict)
                    )
        except Exception as e:
            logger.error(f"Resume Intelligence: OCR extraction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to extract text from the uploaded resume: {str(e)}",
            )

    if not extracted_text.strip():
        return {
            "success": True,
            "document_type": "UNREADABLE",
            "analysis_status": "REJECTED",
            "verification_stopped": True,
            "message": "Could not extract readable text from the uploaded document.",
        }

    logger.info(f"Resume Intelligence: Extracted {len(extracted_text)} chars from '{resume.filename}'.")

    # Step 2: Resume Gate - classify document
    gate_result = classify_as_resume(extracted_text, resume.filename)
    logger.info(f"Resume Intelligence: Gate result: {gate_result['document_type']} (confidence: {gate_result['confidence']:.2f})")

    if not gate_result["is_resume"]:
        return {
            "success": True,
            "document_type": gate_result["document_type"],
            "analysis_status": "REJECTED",
            "verification_stopped": True,
            "gate_confidence": gate_result["confidence"],
            "message": gate_result["reason"],
        }

    # Step 3: Full resume analysis with Skill Passport verification
    logger.info("Resume Intelligence: Running complete analysis pipeline...")
    try:
        analysis = resume_analysis_service.analyze_resume(extracted_text)
    except Exception as e:
        logger.error(f"Resume Intelligence: Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume analysis pipeline failed: {str(e)}",
        )

    logger.info(f"Resume Intelligence: Analysis completed for '{resume.filename}'.")

    return {
        "success": True,
        **analysis,
    }
