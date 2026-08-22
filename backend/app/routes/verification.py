"""
CertiTrust AI - Verification & Hash Lookup Endpoint Router.
Allows querying document status by ID or cryptographic SHA-256 hash.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.document import FullAuditReportResponse, HashVerificationRequest
from app.services.document_service import DocumentService

router = APIRouter(prefix="/verification", tags=["Document Verification"])


@router.get(
    "/{document_id}",
    response_model=FullAuditReportResponse,
    summary="Get Full Verification Audit Report by Document ID",
    description="Retrieves complete audit trail, score breakdown, extracted entities, and fraud flags.",
)
async def get_verification_report(document_id: str):
    """
    Returns complete audit report for a previously ingested document.
    """
    record = await DocumentService.get_document_by_id(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return record["report"]


@router.post(
    "/verify-hash",
    response_model=FullAuditReportResponse,
    summary="Verify Document Authenticity by SHA-256 Hash",
    description="Lookup audit report by SHA-256 hash for Blockchain and zero-knowledge verification.",
)
async def verify_document_by_hash(payload: HashVerificationRequest):
    """
    Verifies document existence and authenticity status by SHA-256 cryptographic hash.
    """
    record = await DocumentService.verify_by_hash(payload.sha256_hash)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verified document found matching hash '{payload.sha256_hash}'.",
        )
    return record["report"]
