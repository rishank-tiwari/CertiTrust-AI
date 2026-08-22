"""
CertiTrust AI - Information Extraction Endpoint Router.
Provides POST /api/v1/extract endpoint accepting raw OCR text and returning structured certificate JSON.
"""

from fastapi import APIRouter, HTTPException, status
from ai.extraction.extraction_service import extraction_service
from app.schemas.extraction import ExtractionRequest, ExtractionResponse
from app.utils.logger import logger

router = APIRouter(prefix="/extract", tags=["Information Extraction"])


@router.post(
    "",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract Structured Fields from OCR Text",
    description="Accepts OCR text input and applies spaCy NER + Regex to extract student name, university, degree, certificate number, issue date, CGPA, and skills.",
)
async def extract_information_from_text(payload: ExtractionRequest):
    """
    Asynchronous endpoint processing OCR text and returning structured entity fields.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input 'text' field cannot be empty.",
        )

    logger.info(f"Received Information Extraction request for text of length: {len(payload.text)} chars")

    try:
        extracted = extraction_service.extract_information(payload.text)
        return ExtractionResponse(**extracted)

    except Exception as e:
        logger.error(f"Error executing Information Extraction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during entity extraction: {str(e)}",
        )
