"""
CertiTrust AI - Pydantic Response Schema for Metadata Analysis Endpoint.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class MetadataResponse(BaseModel):
    """
    Response schema for POST /api/v1/metadata endpoint.
    """

    success: bool = Field(..., example=True)
    metadata: Dict[str, Any] = Field(..., description="Extracted PDF or image properties")
    warnings: List[str] = Field(default_factory=list, description="List of suspicious metadata warning flags")
    risk_level: str = Field(..., example="Medium", description="Risk level classification: Low, Medium, High, Critical")
