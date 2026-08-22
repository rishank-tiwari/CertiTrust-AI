"""
CertiTrust AI - Logo Verification Endpoint Router.
Provides POST /api/v1/logo-verify endpoint accepting certificate (Image/PDF) and reference logo image.
Applies OpenCV multi-scale Template Matching & ORB Keypoint descriptor matching.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.cv_analysis.logo.logo_service import logo_verification_service
from app.schemas.logo import LogoVerificationResponse
from app.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["Computer Vision Logo Verification"])

ALLOWED_CERTIFICATE_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg"}


def validate_upload_files(certificate: UploadFile, reference_logo: UploadFile):
    """
    Validates file extension and size constraints for uploaded files.
    """
    if not certificate.filename or "." not in certificate.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate file must have a valid filename with an extension.",
        )

    cert_ext = certificate.filename.lower().split(".")[-1]
    if cert_ext not in ALLOWED_CERTIFICATE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{cert_ext}' for certificate. Allowed: {', '.join(ALLOWED_CERTIFICATE_EXTENSIONS)}",
        )

    if not reference_logo.filename or "." not in reference_logo.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference logo must have a valid filename with an extension.",
        )

    logo_ext = reference_logo.filename.lower().split(".")[-1]
    if logo_ext not in ALLOWED_LOGO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reference logo format '.{logo_ext}'. Reference logo must be a valid image ({', '.join(ALLOWED_LOGO_EXTENSIONS)}).",
        )


@router.post(
    "/logo-verify",
    response_model=LogoVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Certificate Logo Against Reference Template",
    description="Uploads certificate image/PDF and reference logo image (multipart/form-data). Applies OpenCV template and ORB feature matching.",
)
async def verify_certificate_logo(
    certificate: UploadFile = File(..., description="Uploaded Certificate File (PDF/PNG/JPG/JPEG)"),
    reference_logo: UploadFile = File(..., description="Reference Genuine Logo Image File (PNG/JPG/JPEG)"),
):
    """
    Asynchronous endpoint accepting certificate and reference logo, running logo detection & similarity evaluation.
    """
    logger.info(f"Received Logo Verification request: Certificate='{certificate.filename}', Reference Logo='{reference_logo.filename}'")

    validate_upload_files(certificate, reference_logo)

    cert_bytes = await certificate.read()
    ref_bytes = await reference_logo.read()

    if len(cert_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded certificate file is empty (0 bytes).",
        )

    if len(ref_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded reference logo image is empty (0 bytes).",
        )

    if len(cert_bytes) > settings.MAX_FILE_SIZE or len(ref_bytes) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum permitted limit of {max_mb:.1f} MB.",
        )

    try:
        result = logo_verification_service.verify_logo(
            certificate_bytes=cert_bytes,
            cert_filename=certificate.filename,
            reference_logo_bytes=ref_bytes,
            ref_filename=reference_logo.filename,
        )
        return LogoVerificationResponse(**result)

    except ValueError as ve:
        logger.error(f"Validation Error during Logo Verification: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Internal Error during Logo Verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during Logo Verification: {str(e)}",
        )
