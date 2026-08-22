"""
CertiTrust AI - Core Document Business Service.
Orchestrates file storage, SHA-256 hash generation, AI pipeline processing,
and integration payloads for Frontend and Blockchain smart contracts.
"""

import uuid
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from ai.pipeline import pipeline
from app.config import settings
from app.utils.logger import logger

# In-memory document storage repository for fast hackathon state management
DOCUMENT_REPOSITORY: Dict[str, Dict[str, Any]] = {}
HASH_TO_DOCUMENT_ID: Dict[str, str] = {}


class DocumentService:
    """
    Business service layer managing document lifecycle and AI execution.
    """

    @staticmethod
    async def save_and_process_document(filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Ingests uploaded file, stores it locally, calculates SHA-256 hash,
        and triggers the full CertiTrust AI Pipeline.
        """
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        doc_hash = hashlib.sha256(file_bytes).hexdigest()

        # Ensure upload directory exists
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path = settings.UPLOAD_DIR / f"{document_id}_{filename}"

        # Write file bytes to disk
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        logger.info(f"Saved document to disk: {file_path} (Hash: {doc_hash[:16]}...)")

        # Run AI Pipeline
        ai_result = pipeline.process_document(document_id, filename, file_bytes)

        # Store in repository
        record = {
            "document_id": document_id,
            "filename": filename,
            "file_path": str(file_path),
            "sha256_hash": doc_hash,
            "status": "VERIFIED",
            "report": ai_result,
        }

        DOCUMENT_REPOSITORY[document_id] = record
        HASH_TO_DOCUMENT_ID[doc_hash] = document_id

        return record

    @staticmethod
    async def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches stored document verification record by ID.
        """
        return DOCUMENT_REPOSITORY.get(document_id)

    @staticmethod
    async def verify_by_hash(doc_hash: str) -> Optional[Dict[str, Any]]:
        """
        Lookup document record by SHA-256 hash (used for Blockchain verification matching).
        """
        doc_id = HASH_TO_DOCUMENT_ID.get(doc_hash.lower())
        if doc_id:
            return DOCUMENT_REPOSITORY.get(doc_id)
        return None
