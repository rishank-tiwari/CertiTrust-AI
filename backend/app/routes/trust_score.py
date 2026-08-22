"""
CertiTrust AI - Trust Score Engine Endpoint Router.
Provides POST /api/v1/trust-score endpoint accepting combined AI module outputs and returning composite trust score, authenticity rating, forgery risk, and decision verdict.
"""

from fastapi import APIRouter, HTTPException, status
from ai.trust_score.trust_score_service import trust_score_service
from app.schemas.trust_score import TrustScoreRequest, TrustScoreResponse
from app.utils.logger import logger

router = APIRouter(prefix="/trust-score", tags=["AI Trust Score Engine"])


@router.post(
    "",
    response_model=TrustScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Document Trust Score & Forgery Risk",
    description="Accepts combined outputs from OCR, Information Extraction, Metadata, Computer Vision, and Rule Validation modules. Applies weighted scoring algorithm.",
)
async def calculate_document_trust_score(payload: TrustScoreRequest):
    """
    Asynchronous endpoint executing the centralized AI Trust Score calculation engine.
    """
    logger.info("Received Trust Score calculation request for combined AI module outputs.")

    try:
        result = trust_score_service.calculate_trust_score(
            ocr_data=payload.ocr_data,
            extraction_data=payload.extraction_data,
            metadata_data=payload.metadata_data,
            cv_data=payload.cv_data,
            validation_data=payload.validation_data,
        )
        return TrustScoreResponse(**result)

    except Exception as e:
        logger.error(f"Error executing Trust Score Engine: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during trust score calculation: {str(e)}",
        )
