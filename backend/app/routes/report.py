"""
CertiTrust AI - Explainable AI Report Generator Endpoint Router.
Provides POST /api/v1/report endpoint returning both structured JSON and plain text formatted verification reports.
"""

from fastapi import APIRouter, HTTPException, status
from ai.report.report_service import report_service
from app.schemas.report import ReportRequest, ReportResponse
from app.utils.logger import logger

router = APIRouter(prefix="/report", tags=["Explainable AI Report Generator"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Explainable AI Verification Report",
    description="Accepts structured AI analysis data (Trust Score output & metadata). Generates structured JSON and plain text report internally.",
)
async def generate_ai_verification_report(payload: ReportRequest):
    """
    Asynchronous endpoint generating human-readable explainable AI verification reports internally.
    """
    logger.info("Received Explainable AI Report generation request.")

    try:
        request_dict = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
        result = report_service.generate_report(
            request_data=request_dict,
            ocr_data=payload.ocr_data,
            extraction_data=payload.extraction_data,
            metadata_data=payload.metadata_data,
            cv_data=payload.cv_data,
            validation_data=payload.validation_data,
            trust_score_data=payload.trust_score_data,
        )
        return ReportResponse(**result)

    except Exception as e:
        logger.error(f"Error generating Explainable AI Report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the verification report: {str(e)}",
        )
