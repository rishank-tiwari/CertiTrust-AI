"""
CertiTrust AI - Integrated Computer Vision Analysis FastAPI Router Endpoint.
Provides POST /api/v1/cv-analysis endpoint accepting certificate, reference template, and reference logo.
Executes Logo, Signature, Stamp, Layout, and Tampering detection in one unified call.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.cv_analysis.cv_analysis_service import cv_analysis_service
from app.schemas.cv_analysis import CVAnalysisResponse
from app.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["Integrated Computer Vision Engine"])

ALLOWED_DOC_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg"}


def validate_cv_upload_files(certificate: UploadFile, reference_template: UploadFile, reference_logo: UploadFile):
    """
    Validates uploaded file extensions and size constraints.
    """
    for file_obj, label, allowed in [
        (certificate, "certificate", ALLOWED_DOC_EXTENSIONS),
        (reference_template, "reference_template", ALLOWED_DOC_EXTENSIONS),
        (reference_logo, "reference_logo", ALLOWED_LOGO_EXTENSIONS),
    ]:
        if not file_obj.filename or "." not in file_obj.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{label}' must have a valid filename with an extension.",
            )
        ext = file_obj.filename.lower().split(".")[-1]
        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '.{ext}' for '{label}'. Allowed: {', '.join(allowed)}",
            )


@router.post(
    "/cv-analysis",
    response_model=CVAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Integrated Computer Vision Certificate Analysis",
    description="Uploads certificate (Image/PDF), reference template (Image/PDF), and reference logo (Image). Runs Logo, Signature, Stamp, Layout SSIM, and Tampering detection.",
)
async def perform_integrated_cv_analysis(
    certificate: UploadFile = File(..., description="Uploaded Certificate File (PDF/PNG/JPG/JPEG)"),
    reference_template: UploadFile = File(..., description="Reference Template File (PDF/PNG/JPG/JPEG)"),
    reference_logo: UploadFile = File(..., description="Reference Logo Image File (PNG/JPG/JPEG)"),
):
    """
    Asynchronous endpoint executing all 5 visual document verification stages in one integrated call.
    """
    logger.info(
        f"Received Integrated CV Analysis request: Certificate='{certificate.filename}', "
        f"Reference Template='{reference_template.filename}', Reference Logo='{reference_logo.filename}'"
    )

    validate_cv_upload_files(certificate, reference_template, reference_logo)

    cert_bytes = await certificate.read()
    template_bytes = await reference_template.read()
    logo_bytes = await reference_logo.read()

    if len(cert_bytes) == 0 or len(template_bytes) == 0 or len(logo_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded input files cannot be empty (0 bytes).",
        )

    for b in [cert_bytes, template_bytes, logo_bytes]:
        if len(b) > settings.MAX_FILE_SIZE:
            max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed limit of {max_mb:.1f} MB.",
            )

    try:
        result = cv_analysis_service.analyze_certificate_vision(
            cert_bytes=cert_bytes,
            cert_filename=certificate.filename,
            ref_template_bytes=template_bytes,
            ref_template_filename=reference_template.filename,
            ref_logo_bytes=logo_bytes,
            ref_logo_filename=reference_logo.filename,
        )
        return CVAnalysisResponse(**result)

    except ValueError as ve:
        logger.error(f"Validation Error during Integrated CV Analysis: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Internal Error during Integrated CV Analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during Integrated CV Analysis: {str(e)}",
        )
