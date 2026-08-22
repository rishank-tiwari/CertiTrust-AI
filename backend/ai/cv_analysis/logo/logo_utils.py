"""
CertiTrust AI - Computer Vision Logo Verification Utilities.
Provides OpenCV multi-scale Template Matching, ORB Keypoint & Descriptor Feature Matching,
PDF-to-Image first-page rendering via PyMuPDF, and image validation helpers.
"""

import io
import numpy as np
from typing import Tuple, Dict, Any, Optional
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import cv2
except ImportError:
    cv2 = None

from app.utils.logger import logger


def convert_pdf_first_page_to_bgr(pdf_bytes: bytes) -> np.ndarray:
    """
    Converts the first page of a PDF document into an OpenCV BGR numpy array image using PyMuPDF.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is required for PDF page conversion.")

    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(pdf_doc) == 0:
            raise ValueError("Uploaded PDF file contains no pages.")

        page = pdf_doc.load_page(0)  # Load first page
        zoom = 300 / 72  # Render at 300 DPI high resolution
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        bgr_image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return bgr_image

    except Exception as e:
        logger.error(f"Failed to render first page of PDF: {str(e)}")
        raise ValueError(f"Invalid or corrupted PDF file: {str(e)}")


def decode_image_bytes(file_bytes: bytes, filename: str = "", is_reference_logo: bool = False) -> np.ndarray:
    """
    Decodes raw file bytes into an OpenCV BGR numpy array.
    Automatically handles PDF rendering for certificates and validates image integrity for reference logos.
    """
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) is required for logo verification.")

    is_pdf = filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF")

    # If document is a PDF, render first page to image
    if is_pdf:
        if is_reference_logo:
            raise ValueError("Reference logo must be a valid image file (PNG, JPG, JPEG), not a PDF.")
        logger.info(f"PDF certificate detected for file '{filename}'. Converting page 1 to image...")
        return convert_pdf_first_page_to_bgr(file_bytes)

    # Standard Image Decoding (PNG, JPG, JPEG)
    try:
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            # Fallback to PIL
            pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        return image

    except Exception as e:
        field_label = "Reference logo" if is_reference_logo else "Certificate file"
        logger.error(f"Failed to decode image bytes for {field_label} '{filename}': {str(e)}")
        raise ValueError(f"{field_label} '{filename}' is not a valid image file: {str(e)}")


def perform_template_matching(certificate_bgr: np.ndarray, reference_bgr: np.ndarray) -> Tuple[float, Optional[Tuple[int, int, int, int]]]:
    """
    Executes multi-scale OpenCV template matching to locate logo region and return max correlation score.

    Returns:
        Tuple[float, Optional[Tuple[int, int, int, int]]]: (similarity_ratio [0.0 - 1.0], bounding_box (x, y, w, h))
    """
    if cv2 is None:
        return 0.0, None

    cert_gray = cv2.cvtColor(certificate_bgr, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2GRAY)

    c_h, c_w = cert_gray.shape[:2]
    r_h, r_w = ref_gray.shape[:2]

    if r_h > c_h or r_w > c_w:
        scale = min(c_h / r_h, c_w / r_w) * 0.4
        new_w = max(10, int(r_w * scale))
        new_h = max(10, int(r_h * scale))
        ref_gray = cv2.resize(ref_gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
        r_h, r_w = new_h, new_w

    best_val = -1.0
    best_loc = (0, 0)
    best_scale_dim = (r_w, r_h)

    scales = [0.5, 0.75, 1.0, 1.25, 1.5]
    for scale in scales:
        resized_w = int(r_w * scale)
        resized_h = int(r_h * scale)

        if resized_h >= c_h or resized_w >= c_w or resized_w < 10 or resized_h < 10:
            continue

        scaled_ref = cv2.resize(ref_gray, (resized_w, resized_h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(cert_gray, scaled_ref, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale_dim = (resized_w, resized_h)

    template_score = max(0.0, float(best_val))
    bbox = (best_loc[0], best_loc[1], best_scale_dim[0], best_scale_dim[1])

    return template_score, bbox


def perform_orb_feature_matching(certificate_bgr: np.ndarray, reference_bgr: np.ndarray) -> float:
    """
    Executes ORB (Oriented FAST and Rotated BRIEF) keypoint detection & Hamming distance matching.

    Returns:
        float: Feature matching score ratio [0.0 - 1.0]
    """
    if cv2 is None:
        return 0.0

    cert_gray = cv2.cvtColor(certificate_bgr, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(reference_bgr, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=1000)

    kp1, des1 = orb.detectAndCompute(ref_gray, None)
    kp2, des2 = orb.detectAndCompute(cert_gray, None)

    if des1 is None or des2 is None or len(kp1) == 0 or len(kp2) == 0:
        return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    if not matches:
        return 0.0

    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = [m for m in matches if m.distance < 50]
    match_ratio = len(good_matches) / max(1, len(kp1))

    feature_score = min(1.0, match_ratio * 2.5)
    return float(feature_score)


def calculate_hybrid_similarity(template_score: float, feature_score: float) -> Tuple[float, str, str]:
    """
    Calculates final composite similarity score (0.0% to 100.0%), confidence level, and match status.

    Returns:
        Tuple[float, str, str]: (similarity_score_pct, confidence ['High'|'Medium'|'Low'], status ['Matched'|'Mismatched'])
    """
    if template_score >= 0.85:
        combined = (template_score * 0.80) + (feature_score * 0.20)
    else:
        combined = (template_score * 0.50) + (feature_score * 0.50)

    similarity_pct = round(min(100.0, max(0.0, combined * 100.0)), 1)

    if similarity_pct >= 70.0 or template_score >= 0.85:
        confidence = "High"
        status = "Matched"
    elif similarity_pct >= 45.0:
        confidence = "Medium"
        status = "Matched" if similarity_pct >= 50.0 else "Mismatched"
    else:
        confidence = "Low"
        status = "Mismatched"

    return similarity_pct, confidence, status
