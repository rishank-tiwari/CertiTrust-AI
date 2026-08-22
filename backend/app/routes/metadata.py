"""
CertiTrust AI - Metadata Analysis Endpoint Router.
Provides POST /api/v1/metadata endpoint supporting PDF, PNG, JPG, JPEG files.
Extracts file metadata and identifies suspicious manipulation flags.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.metadata.metadata_service import metadata_service
from app.schemas.metadata import MetadataResponse
from app.config import settings
from app.utils.logger import logger

router = APIRouter(prefix="/metadata", tags=["Metadata Analysis"])

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def validate_file(filename: str, file_size: int):
    """
    Validates uploaded file extension and maximum file size constraint.
    """
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. File must have a valid extension.",
        )

    ext = filename.lower().split(".")[-1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {max_mb:.1f} MB.",
        )


@router.post(
    "",
    response_model=MetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract & Validate Document Metadata",
    description="Accepts PDF, PNG, JPG, or JPEG file. Extracts creator, dates, EXIF headers, and identifies suspicious editing flags.",
)
async def analyze_document_metadata(file: UploadFile = File(...)):
    """
    Asynchronous endpoint accepting UploadFile, validating constraints, and returning metadata analysis payload.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    logger.info(f"Received Metadata Analysis request for file: '{file.filename}'")

    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    validate_file(file.filename, file_size)

    try:
        result = metadata_service.analyze_metadata(file_bytes, file.filename)
        return MetadataResponse(**result)

    except ValueError as ve:
        logger.error(f"Validation Error for file '{file.filename}': {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Internal Error during metadata extraction for '{file.filename}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing metadata: {str(e)}",
        )
