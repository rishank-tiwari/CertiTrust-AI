"""
CertiTrust AI - Pydantic Request & Response Schemas for Trust Score Engine.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class TrustScoreRequest(BaseModel):
    """
    Request payload accepting combined outputs from OCR, Extraction, Metadata, CV, and Validation modules.
    """

    ocr_data: Dict[str, Any] = Field(default_factory=dict, description="Output payload from OCR module")
    extraction_data: Dict[str, Any] = Field(default_factory=dict, description="Output payload from Information Extraction module")
    metadata_data: Dict[str, Any] = Field(default_factory=dict, description="Output payload from Metadata Analysis module")
    cv_data: Dict[str, Any] = Field(default_factory=dict, description="Output payload from Computer Vision module")
    validation_data: Dict[str, Any] = Field(default_factory=dict, description="Output payload from Rule Validation module")


class ScoreBreakdown(BaseModel):
    """
    Weighted contribution score breakdown dictionary.
    """

    ocr: int = Field(..., example=14, description="OCR completeness contribution (max 15)")
    information_extraction: int = Field(..., example=20, description="Structured Extraction contribution (max 20)")
    metadata: int = Field(..., example=15, description="Metadata analysis contribution (max 15)")
    computer_vision: int = Field(..., example=32, description="Computer vision contribution (max 35)")
    validation: int = Field(..., example=14, description="Rule validation contribution (max 15)")


class TrustScoreResponse(BaseModel):
    """
    Response schema for POST /api/v1/trust-score endpoint.
    """

    success: bool = Field(..., example=True)
    authenticity_score: int = Field(..., example=94, ge=0, le=100, description="Authenticity percentage score (0-100)")
    trust_score: int = Field(..., example=92, ge=0, le=100, description="Composite trust score (0-100)")
    forgery_risk: str = Field(..., example="Low", description="Forgery risk classification: Very Low, Low, Medium, High, Critical")
    decision: str = Field(..., example="Verified", description="Final verdict: Verified, Needs Manual Review, Suspicious, Likely Forged")
    score_breakdown: ScoreBreakdown = Field(..., description="Individual weighted score contribution breakdown")
