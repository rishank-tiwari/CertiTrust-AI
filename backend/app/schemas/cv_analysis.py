"""
CertiTrust AI - Pydantic Response Schema for Integrated Computer Vision Analysis Endpoint.
"""

from pydantic import BaseModel, Field


class CVAnalysisResponse(BaseModel):
    """
    Response schema for POST /api/v1/cv-analysis endpoint.
    """

    success: bool = Field(..., example=True)
    logo_score: int = Field(..., example=97, ge=0, le=100, description="Logo verification score (0-100)")
    signature_score: int = Field(..., example=92, ge=0, le=100, description="Signature detection score (0-100)")
    stamp_score: int = Field(..., example=94, ge=0, le=100, description="Stamp/seal detection score (0-100)")
    layout_score: int = Field(..., example=95, ge=0, le=100, description="Layout SSIM + ORB similarity score (0-100)")
    tampering_score: int = Field(..., example=5, ge=0, le=100, description="Tampering artifact score (0-100, lower is cleaner)")
    tampering_detected: bool = Field(..., example=False, description="Flag indicating detected tampering artifacts")
    overall_cv_score: int = Field(..., example=95, ge=0, le=100, description="Weighted composite CV score (0-100)")
