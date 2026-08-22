"""
CertiTrust AI - Unified AI Pipeline Analyze Endpoint Router.
Provides POST /api/v1/analyze endpoint executing the complete 7-stage AI verification pipeline in sequence.
"""

from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.pipeline.analysis_service import pipeline_analysis_service
from app.schemas.analyze import ConsolidatedAnalysisResponse
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/analyze", tags=["Unified AI Pipeline Orchestrator"])

ALLOWED_DOC_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg"}


@router.post(
    "",
    response_model=ConsolidatedAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Complete End-to-End AI Verification Pipeline",
    description="Single unified entry point for frontend verification. Runs OCR -> Extraction -> Metadata -> Computer Vision -> Validation -> Trust Score -> Explainable AI Report in sequence.",
)
async def analyze_credential_pipeline(
    certificate: UploadFile = File(..., description="Uploaded Certificate File (PDF/PNG/JPG/JPEG)"),
    reference_template: Optional[UploadFile] = File(None, description="Optional Reference Template File (PDF/PNG/JPG/JPEG)"),
    reference_logo: Optional[UploadFile] = File(None, description="Optional Reference Logo Image File (PNG/JPG/JPEG)"),
):
    """
    Asynchronous unified endpoint executing the complete end-to-end AI document verification pipeline.
    """
    logger.info(f"Received Unified Pipeline Analyze request for certificate: '{certificate.filename}'")

    # Validate Certificate File Extension
    if not certificate.filename or "." not in certificate.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded certificate must have a valid filename with an extension.",
        )

    cert_ext = certificate.filename.lower().split(".")[-1]
    if cert_ext not in ALLOWED_DOC_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{cert_ext}' for certificate. Allowed: {', '.join(ALLOWED_DOC_EXTENSIONS)}",
        )

    cert_bytes = await certificate.read()
    if len(cert_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded certificate file cannot be empty (0 bytes).",
        )

    if len(cert_bytes) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Certificate file size exceeds maximum permitted limit of {max_mb:.1f} MB.",
        )

    # Read optional reference template
    ref_template_bytes = None
    ref_template_name = None
    if reference_template and reference_template.filename:
        ref_template_bytes = await reference_template.read()
        ref_template_name = reference_template.filename

    # Read optional reference logo
    ref_logo_bytes = None
    ref_logo_name = None
    if reference_logo and reference_logo.filename:
        ref_logo_bytes = await reference_logo.read()
        ref_logo_name = reference_logo.filename

    try:
        result = pipeline_analysis_service.run_full_pipeline(
            cert_bytes=cert_bytes,
            cert_filename=certificate.filename,
            ref_template_bytes=ref_template_bytes,
            ref_template_filename=ref_template_name,
            ref_logo_bytes=ref_logo_bytes,
            ref_logo_filename=ref_logo_name,
        )
        return ConsolidatedAnalysisResponse(**result)

    except Exception as e:
        logger.error(f"Error during Unified Pipeline Analysis for '{certificate.filename}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during AI pipeline analysis: {str(e)}",
        )
