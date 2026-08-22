"""
CertiTrust AI - Production Metadata Analysis Service Module.
Orchestrates PDF and image metadata extraction and runs suspicious rule-based validation.
"""

from typing import Dict, Any
from ai.metadata.metadata_utils import (
    extract_pdf_metadata_fitz,
    extract_image_metadata_pil,
    validate_suspicious_metadata,
)
from app.utils.logger import logger

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


class MetadataService:
    """
    Metadata Analysis Service managing metadata parsing and suspicious rule validation.
    """

    def analyze_metadata(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extracts metadata from PDF or Image file bytes and runs suspicious security checks.

        Returns:
            Dict[str, Any]: JSON object with success status, metadata details, warnings list, and risk_level.
        """
        logger.info(f"Starting Metadata Analysis for file: '{filename}' (Size: {len(file_bytes)} bytes)")
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        if ext not in ALLOWED_EXTENSIONS:
            logger.error(f"Metadata extraction failed: Unsupported file extension '.{ext}' for file '{filename}'")
            raise ValueError(f"Unsupported file extension '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

        is_pdf = (ext == "pdf") or file_bytes.startswith(b"%PDF")

        try:
            if is_pdf:
                raw_meta = extract_pdf_metadata_fitz(file_bytes, filename)
                display_metadata = {
                    "file_name": raw_meta["file_name"],
                    "file_size_bytes": raw_meta["file_size_bytes"],
                    "creator": raw_meta.get("creator"),
                    "producer": raw_meta.get("producer"),
                    "author": raw_meta.get("author"),
                    "subject": raw_meta.get("subject"),
                    "title": raw_meta.get("title"),
                    "creation_date": raw_meta.get("creation_date"),
                    "modification_date": raw_meta.get("modification_date"),
                    "pdf_version": raw_meta.get("pdf_version"),
                    "pages": raw_meta.get("total_pages", 1),
                    "encrypted": raw_meta.get("encrypted", False),
                }
            else:
                raw_meta = extract_image_metadata_pil(file_bytes, filename)
                display_metadata = {
                    "file_name": raw_meta["file_name"],
                    "file_size_bytes": raw_meta["file_size_bytes"],
                    "width": raw_meta.get("width"),
                    "height": raw_meta.get("height"),
                    "dpi": raw_meta.get("dpi"),
                    "format": raw_meta.get("format"),
                    "color_mode": raw_meta.get("color_mode"),
                    "creation_time": raw_meta.get("creation_time"),
                    "software_exif": raw_meta.get("software_exif"),
                }

            # Run suspicious rule-based validator
            warnings, risk_level = validate_suspicious_metadata(raw_meta, is_pdf=is_pdf)

            logger.info(
                f"Metadata Extraction Success for '{filename}'. File Type: {'PDF' if is_pdf else 'IMAGE'}, "
                f"Warnings Count: {len(warnings)}, Risk Level: '{risk_level}'"
            )

            if warnings:
                logger.warning(f"Suspicious metadata flags for '{filename}': {warnings}")

            return {
                "success": True,
                "metadata": display_metadata,
                "warnings": warnings,
                "risk_level": risk_level,
            }

        except Exception as e:
            logger.error(f"Error during metadata extraction for file '{filename}': {str(e)}")
            raise RuntimeError(f"Metadata extraction failed: {str(e)}")


# Global Singleton Service Instance
metadata_service = MetadataService()
