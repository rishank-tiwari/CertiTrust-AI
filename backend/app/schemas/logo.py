"""
CertiTrust AI - Pydantic Response Schema for Logo Verification Endpoint.
"""

from pydantic import BaseModel, Field


class LogoVerificationResponse(BaseModel):
    """
    Response schema for POST /api/v1/logo-verify endpoint.
    """

    success: bool = Field(..., example=True)
    logo_detected: bool = Field(..., example=True, description="Indicates if logo region was found")
    similarity_score: float = Field(..., example=97.8, ge=0.0, le=100.0, description="Similarity score percentage (0-100%)")
    confidence: str = Field(..., example="High", description="Confidence rating: High, Medium, Low")
    status: str = Field(..., example="Matched", description="Verification verdict: Matched, Mismatched")
