"""
CertiTrust AI - Pydantic Response Schema for Unified Pipeline Analyze Endpoint.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ConsolidatedAnalysisResponse(BaseModel):
    """
    Consolidated response schema for POST /api/v1/analyze endpoint.
    Handles both successful pipeline runs and early pipeline termination for unsupported media.
    """

    success: bool = Field(..., example=True)
    execution_time_seconds: Optional[float] = Field(default=None, example=0.15, description="Total pipeline execution time in seconds")
    document_type: Optional[str] = Field(default=None, example="Academic Certificate", description="Classified document type")
    is_supported: Optional[bool] = Field(default=None, example=True, description="Indicates if uploaded file is a supported credential")
    confidence: Optional[float] = Field(default=None, example=0.95, description="Document type classification confidence")
    reason: Optional[str] = Field(default=None, example="Successfully classified document as a valid 'Academic Certificate'.")
    message: Optional[str] = Field(default=None, example="Supported academic credential verified.")
    verification_stopped: Optional[bool] = Field(default=False, description="True if verification was stopped early")
    classification: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 0: Document Classification")
    ocr: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 1: OCR Engine")
    information_extraction: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 2: Information Extraction")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 3: Metadata Analysis")
    computer_vision: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 4: Computer Vision Analysis")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 5: Rule Validation Engine")
    trust_score: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 6: Centralized Trust Score Engine")
    report: Optional[Dict[str, Any]] = Field(default=None, description="Output payload from Step 7: Explainable AI Report Generator")
