"""
CertiTrust AI - Document Upload & OCR FastAPI Router Endpoint.
Provides POST /api/v1/upload endpoint supporting PDF, PNG, JPG, JPEG files.
Validates file extension & max size, runs OpenCV + PaddleOCR pipeline, and returns JSON.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ai.ocr.ocr_service import ocr_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["OCR Document Upload"])

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
    "/upload",
    status_code=status.HTTP_200_OK,
    summary="Upload Document for OCR Processing",
    description="Uploads a PDF, PNG, JPG, or JPEG file. Applies OpenCV preprocessing & PaddleOCR to extract text per page.",
)
async def upload_document_for_ocr(file: UploadFile = File(...)):
    """
    Asynchronous endpoint accepting UploadFile, validating constraints, and returning OCR JSON payload.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    logger.info(f"Received OCR upload request for file: '{file.filename}'")

    # Read file content into memory
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # Validate file type & size
    validate_file(file.filename, file_size)

    try:
        # Execute OCR processing pipeline
        ocr_result = ocr_service.process_document(file_bytes, file.filename)
        return ocr_result

    except ValueError as ve:
        logger.error(f"Validation Error processing file '{file.filename}': {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.error(f"Internal Error during OCR processing for '{file.filename}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing OCR: {str(e)}",
        )
