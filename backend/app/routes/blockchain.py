"""
CertiTrust AI - Blockchain & Web3 Integration Endpoint Router.
Formats verification results into standardized payloads for Smart Contract submission.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.document import BlockchainPayloadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/blockchain", tags=["Blockchain Integration"])


@router.get(
    "/payload/{document_id}",
    response_model=BlockchainPayloadResponse,
    summary="Get Web3 Smart Contract Payload",
    description="Returns pre-formatted JSON payload matching Solidity smart contract struct for on-chain credential registry.",
)
async def get_blockchain_payload(document_id: str):
    """
    Retrieves web3-ready payload for a verified document.
    """
    record = await DocumentService.get_document_by_id(document_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    report = record["report"]
    bc = report["blockchain_ready_payload"]

    return BlockchainPayloadResponse(
        doc_hash=bc["doc_hash"],
        cert_id=str(bc.get("cert_id") or ""),
        issuer=str(bc.get("issuer") or ""),
        recipient=str(bc.get("recipient") or ""),
        trust_score_scaled=int(bc.get("trust_score_scaled", bc.get("score", 0))),
        timestamp=int(bc["timestamp"]),
        is_valid=bool(bc.get("is_valid", report["verdict"]["is_authentic"])),
    )
