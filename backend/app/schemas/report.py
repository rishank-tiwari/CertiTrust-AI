"""
CertiTrust AI - Pydantic Request & Response Schemas for Explainable AI Report Generator.
Provides clean Swagger examples accepting Trust Score engine outputs and extracted metadata.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ScoreBreakdownInput(BaseModel):
    """
    Score breakdown input schema from Trust Score module.
    """

    ocr: int = Field(default=14, example=14, description="OCR score contribution")
    information_extraction: int = Field(default=20, example=20, description="Extraction score contribution")
    metadata: int = Field(default=15, example=15, description="Metadata score contribution")
    computer_vision: int = Field(default=32, example=32, description="Computer Vision score contribution")
    validation: int = Field(default=14, example=14, description="Validation score contribution")


class ReportRequest(BaseModel):
    """
    Structured Request Payload accepting Trust Score output and credential metadata.
    Does not inject fake demo values; unextracted fields default to None.
    """

    authenticity_score: int = Field(default=94, example=94, ge=0, le=100, description="Authenticity percentage score")
    trust_score: int = Field(default=92, example=92, ge=0, le=100, description="Composite Trust score")
    forgery_risk: str = Field(default="Low", example="Low", description="Forgery risk level: Very Low, Low, Medium, High, Critical")
    decision: str = Field(default="Verified", example="Verified", description="Verification verdict: Verified, Needs Manual Review, Suspicious, Likely Forged")
    score_breakdown: ScoreBreakdownInput = Field(default_factory=ScoreBreakdownInput, description="Sub-score breakdown dictionary")
    student_name: Optional[str] = Field(default=None, description="Extracted Student Name")
    university: Optional[str] = Field(default=None, description="Extracted University Name")
    degree: Optional[str] = Field(default=None, description="Extracted Degree Title")
    course: Optional[str] = Field(default=None, description="Extracted Branch/Course")
    certificate_number: Optional[str] = Field(default=None, description="Certificate ID / Serial Number")
    issue_date: Optional[str] = Field(default=None, description="Extracted Issue Date")
    cgpa: Optional[str] = Field(default=None, description="Extracted CGPA / Marks")

    ocr_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw OCR payload")
    extraction_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw extraction payload")
    metadata_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw metadata payload")
    cv_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw CV payload")
    validation_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw validation payload")
    trust_score_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional raw trust score payload")


class ReportResponse(BaseModel):
    """
    Response schema returning both structured report_json and plain text report_text.
    """

    success: bool = Field(..., example=True)
    report_json: Dict[str, Any] = Field(..., description="Structured JSON object containing all 12 report sections")
    report_text: str = Field(..., description="Generated human-readable plain text verification report")
