"""
CertiTrust AI - Rule Validation Endpoint Router.
Provides POST /api/v1/validate endpoint accepting combined AI module outputs and returning rule evaluation results.
"""

from fastapi import APIRouter, HTTPException, status
from ai.validation.validation_service import rule_validation_service
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.utils.logger import logger

router = APIRouter(prefix="/validate", tags=["Rule Validation Engine"])


@router.post(
    "",
    response_model=ValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Credential Against 10 Authenticity Rules",
    description="Accepts combined outputs from OCR, Information Extraction, Metadata, and Computer Vision modules. Evaluates 10 authenticity rules and computes validation score.",
)
async def validate_credential_rules(payload: ValidationRequest):
    """
    Asynchronous endpoint executing the 10-rule authenticity evaluation engine.
    """
    logger.info("Received Rule Validation request for combined AI module outputs.")

    try:
        result = rule_validation_service.validate_credential(
            ocr_data=payload.ocr_data,
            extraction_data=payload.extraction_data,
            metadata_data=payload.metadata_data,
            cv_data=payload.cv_data,
            logo_threshold=payload.logo_threshold or 70,
            signature_threshold=payload.signature_threshold or 70,
            layout_threshold=payload.layout_threshold or 70,
        )
        return ValidationResponse(**result)

    except Exception as e:
        logger.error(f"Error during Rule Validation execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during rule validation: {str(e)}",
        )
