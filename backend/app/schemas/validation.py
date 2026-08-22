"""
CertiTrust AI - Pydantic Request & Response Schemas for Rule Validation Engine.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """
    Request schema accepting combined outputs from OCR, Extraction, Metadata, and Computer Vision modules.
    """

    ocr_data: Dict[str, Any] = Field(default_factory=dict, description="Output dictionary from OCR module")
    extraction_data: Dict[str, Any] = Field(default_factory=dict, description="Output dictionary from Information Extraction module")
    metadata_data: Dict[str, Any] = Field(default_factory=dict, description="Output dictionary from Metadata Analysis module")
    cv_data: Dict[str, Any] = Field(default_factory=dict, description="Output dictionary from Computer Vision module")
    logo_threshold: Optional[int] = Field(default=70, description="Configurable minimum logo score threshold")
    signature_threshold: Optional[int] = Field(default=70, description="Configurable minimum signature score threshold")
    layout_threshold: Optional[int] = Field(default=70, description="Configurable minimum layout score threshold")


class RuleResultItem(BaseModel):
    """
    Schema for individual rule result entry.
    """

    rule: str = Field(..., example="Logo Verification")
    passed: bool = Field(..., example=True)
    reason: str = Field(..., example="Logo similarity is above threshold.")


class ValidationResponse(BaseModel):
    """
    Response schema for POST /api/v1/validate endpoint.
    """

    success: bool = Field(..., example=True)
    validation_results: List[RuleResultItem] = Field(..., description="List of rule evaluation outcomes")
    passed_rules: int = Field(..., example=9, description="Count of passed rules")
    failed_rules: int = Field(..., example=1, description="Count of failed rules")
    validation_score: int = Field(..., example=90, ge=0, le=100, description="Overall rule validation percentage score")
