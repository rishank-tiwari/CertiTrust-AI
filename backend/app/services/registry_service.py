"""
CertiTrust AI - Credential Registry Service.
Provides database/storage abstraction layer for registering and retrieving Canonical Credential Records.
Completely decouples AI extraction logic from database storage.
"""

import time
from typing import Dict, Any, Optional
from app.utils.logger import logger


class CredentialRegistryService:
    """
    Simulated Repository/Registry service for Canonical Credential Records.
    Thread-safe in-memory store mimicking database operations.
    """
    _instance = None
    _db: Dict[str, Dict[str, Any]] = {}
    _hash_db: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CredentialRegistryService, cls).__new__(cls)
        return cls._instance

    def register(self, record: Dict[str, Any]) -> None:
        """
        Stores canonical record in registry index databases.
        """
        cred_id = record["credential_id"]
        doc_hash = record["document"]["sha256"]
        self._db[cred_id] = record
        self._hash_db[doc_hash] = record
        logger.info(f"Registered Canonical Credential Record: {cred_id} | Hash: {doc_hash}")

    def get_by_id(self, cred_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves record by Credential ID.
        """
        return self._db.get(cred_id)

    def get_by_hash(self, doc_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves record by SHA-256 document hash.
        """
        return self._hash_db.get(doc_hash)

    def clear(self) -> None:
        """
        Clears all registry records (used for test resets).
        """
        self._db.clear()
        self._hash_db.clear()


# Global Singleton Registry Service
credential_registry = CredentialRegistryService()
