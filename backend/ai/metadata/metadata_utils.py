"""
CertiTrust AI - Metadata Extraction & Inspection Utilities.
Helper functions for extracting PDF headers, image EXIF properties, and date difference calculations.
"""

import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ExifTags

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from app.utils.logger import logger

# List of known document editing tools
EDITING_SOFTWARE_KEYWORDS = [
    "photoshop", "gimp", "illustrator", "canva", "inkscape", "paint.net",
    "pdfescape", "acrobat", "indesign", "coreldraw", "affinity", "pixlr",
]


def extract_pdf_metadata_fitz(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Extracts PDF metadata (creator, producer, dates, pages, version, encryption) using PyMuPDF.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is required for PDF metadata extraction.")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    meta = doc.metadata or {}

    total_pages = len(doc)
    is_encrypted = doc.is_encrypted
    pdf_version = f"1.{doc.pdf_version()}" if hasattr(doc, "pdf_version") else "1.4"

    creation_date = parse_pdf_date(meta.get("creationDate"))
    mod_date = parse_pdf_date(meta.get("modDate"))

    pdf_metadata = {
        "file_name": filename,
        "file_size_bytes": len(file_bytes),
        "total_pages": total_pages,
        "pdf_version": pdf_version,
        "creator": meta.get("creator") or None,
        "producer": meta.get("producer") or None,
        "author": meta.get("author") or None,
        "subject": meta.get("subject") or None,
        "title": meta.get("title") or None,
        "creation_date": creation_date,
        "modification_date": mod_date,
        "encrypted": is_encrypted,
        "raw_metadata": meta,
    }

    return pdf_metadata


def extract_image_metadata_pil(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Extracts image metadata (width, height, DPI, format, color mode, EXIF headers) using Pillow.
    """
    img = Image.open(io.BytesIO(file_bytes))

    width, height = img.size
    img_format = img.format or filename.split(".")[-1].upper()
    color_mode = img.mode

    # Extract DPI
    dpi_info = img.info.get("dpi")
    if dpi_info and isinstance(dpi_info, tuple) and len(dpi_info) >= 2:
        dpi = int(dpi_info[0])
    else:
        dpi = 72  # Default fallback DPI

    # Extract EXIF Metadata
    exif_data = {}
    creation_time = None
    software_exif = None

    try:
        exif = img.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                # Store string or int representations
                if isinstance(value, (str, int, float)):
                    exif_data[tag_name] = value

                if tag_name.lower() in ("datetime", "datetimeoriginal", "datetimedigitized"):
                    creation_time = str(value)
                if tag_name.lower() == "software":
                    software_exif = str(value)
    except Exception as e:
        logger.warning(f"EXIF parsing warning for '{filename}': {str(e)}")

    image_metadata = {
        "file_name": filename,
        "file_size_bytes": len(file_bytes),
        "width": width,
        "height": height,
        "dpi": dpi,
        "format": img_format,
        "color_mode": color_mode,
        "creation_time": creation_time,
        "software_exif": software_exif,
        "exif": exif_data,
    }

    return image_metadata


def parse_pdf_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parses PDF metadata date strings (e.g., 'D:20260315120000+00\'00\'') into ISO format.
    """
    if not date_str or not isinstance(date_str, str):
        return None

    cleaned = date_str.replace("D:", "").replace("'", "")
    try:
        if len(cleaned) >= 8:
            year = cleaned[:4]
            month = cleaned[4:6]
            day = cleaned[6:8]
            return f"{year}-{month}-{day}"
    except Exception:
        pass

    return date_str


def validate_suspicious_metadata(meta_dict: Dict[str, Any], is_pdf: bool) -> Tuple[List[str], str]:
    """
    Rule-based validator checking metadata for manipulation indicators.
    Returns:
        Tuple[List[str], str]: (warnings list, risk_level string: 'Low', 'Medium', 'High', 'Critical')
    """
    warnings: List[str] = []
    risk_score = 0

    if is_pdf:
        creator = str(meta_dict.get("creator") or "").lower()
        producer = str(meta_dict.get("producer") or "").lower()
        author = str(meta_dict.get("author") or "").lower()

        # Check 1: Editing Software Flags in Creator / Producer
        for tool in EDITING_SOFTWARE_KEYWORDS:
            if tool in creator or tool in producer or tool in author:
                warnings.append(f"Document edited using {tool.capitalize()}.")
                risk_score += 35
                break

        # Check 2: Encryption Status
        if meta_dict.get("encrypted"):
            warnings.append("PDF document is encrypted.")
            risk_score += 15

        # Check 3: Missing Metadata Warning
        if not meta_dict.get("creator") and not meta_dict.get("producer") and not meta_dict.get("author"):
            warnings.append("Document metadata is stripped or missing.")
            risk_score += 20

        # Check 4: Creation vs Modification Date Discrepancy
        c_date = meta_dict.get("creation_date")
        m_date = meta_dict.get("modification_date")
        if c_date and m_date and c_date != m_date:
            warnings.append("Modification date is significantly later than creation date.")
            risk_score += 25

    else:
        # Image Files
        exif = meta_dict.get("exif", {})
        software = str(meta_dict.get("software_exif") or "").lower()

        for tool in EDITING_SOFTWARE_KEYWORDS:
            if tool in software or any(tool in str(v).lower() for v in exif.values()):
                warnings.append(f"Image EXIF contains editing software metadata ({tool.capitalize()}).")
                risk_score += 35
                break

        if not exif:
            warnings.append("Image EXIF metadata is missing or stripped.")
            risk_score += 15

    # Determine Risk Level
    if risk_score == 0:
        risk_level = "Low"
    elif risk_score <= 30:
        risk_level = "Medium"
    elif risk_score <= 60:
        risk_level = "High"
    else:
        risk_level = "Critical"

    return warnings, risk_level
