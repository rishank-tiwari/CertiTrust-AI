"""
CertiTrust AI - Pydantic Request & Response Schemas.
Standardized interfaces for Frontend Dashboard & Blockchain Smart Contract integration.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """
    Response model returned immediately upon document ingestion & processing.
    """

    document_id: str = Field(..., example="doc_a1b2c3d4e5f6")
    filename: str = Field(..., example="degree_certificate.pdf")
    sha256_hash: str = Field(..., example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    status: str = Field(..., example="VERIFIED")
    trust_score: float = Field(..., example=96.5)
    is_authentic: bool = Field(..., example=True)
    risk_level: str = Field(..., example="LOW")


class AnalysisRequest(BaseModel):
    """
    Schema for requesting manual re-analysis or custom AI pipeline runs.
    """

    document_id: str = Field(..., description="Unique document ID to analyze")
    enable_ocr: bool = Field(default=True, description="Flag to enable OCR engine")
    enable_fraud_check: bool = Field(default=True, description="Flag to enable AI fraud detection")


class HashVerificationRequest(BaseModel):
    """
    Request model for verifying a document by its SHA-256 cryptographic hash.
    """

    sha256_hash: str = Field(..., description="Cryptographic SHA-256 hash of the document")


class BlockchainPayloadResponse(BaseModel):
    """
    Standardized payload format ready to submit to Web3 / Smart Contract verification function.
    """

    doc_hash: str = Field(..., description="Document SHA-256 hash")
    cert_id: str = Field(..., description="Extracted certificate ID")
    issuer: str = Field(..., description="Issuer authority name")
    recipient: str = Field(..., description="Recipient candidate name")
    trust_score_scaled: int = Field(..., description="Trust score multiplied by 100 for uint256 precision")
    timestamp: int = Field(..., description="Unix timestamp of verification")
    is_valid: bool = Field(..., description="Authenticity flag")


class FullAuditReportResponse(BaseModel):
    """
    Comprehensive verification audit report for frontend display.
    """

    audit_id: str
    document_id: str
    filename: str
    document_sha256_hash: str
    verification_timestamp: str
    verdict: Dict[str, Any]
    extracted_certificate_details: Dict[str, Any]
    fraud_analysis: Dict[str, Any]
    technical_breakdown: Dict[str, Any]
    blockchain_ready_payload: BlockchainPayloadResponse
