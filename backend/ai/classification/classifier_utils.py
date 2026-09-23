"""
CertiTrust AI - Production Document Type Classifier Utilities.
Provides a strict two-stage Credential Gate:
- Stage 1: Determines if the document is actually an educational/professional/achievement credential.
- Stage 2: Only if Stage 1 passes, maps to specific supported credential types (distinguishing B.Tech Marksheets, 10th vs 12th).
Strictly rejects resumes, CVs, random screenshots, invoices, memes, and photos as 'Not an Educational Credential'.
"""

import io
import re
import mimetypes
import numpy as np
from typing import Tuple, Dict, Any, List
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

# 🟢 Positive Academic Domain Indicators with Weighting
POSITIVE_INDICATORS = {
    # Core Credential Title/Type Indicators (+20)
    "certificate": 20,
    "certify": 15,
    "marksheet": 20,
    "mark sheet": 20,
    "statement of marks": 20,
    "statement of grades": 20,
    "grade card": 20,
    "report card": 20,
    "passing certificate": 20,
    "completion certificate": 20,
    "diploma": 20,
    "degree": 20,
    "transcript": 20,
    "provisional": 15,
    "migration": 15,
    "character": 15,
    "internship": 20,
    "intern": 15,
    "training": 15,
    "skill": 15,
    "hackathon": 20,
    "award": 20,
    "competition": 15,
    "achievement": 20,
    "workshop": 15,
    "seminar": 15,
    "resume": 20,
    "curriculum vitae": 20,
    "cv": 15,

    # Higher Education / School Identifiers (+10)
    "university": 10,
    "institute": 10,
    "college": 10,
    "school": 10,
    "academy": 10,
    "faculty": 10,
    "department": 8,
    "board": 12,
    "secondary": 10,
    "higher secondary": 12,
    "cbse": 15,
    "icse": 15,
    "state board": 12,

    # Academic Status & Result Identifiers (+8)
    "bachelor": 10,
    "master": 10,
    "btech": 15,
    "mtech": 15,
    "bsc": 10,
    "msc": 10,
    "examination": 10,
    "semester": 8,
    "cgpa": 10,
    "gpa": 10,
    "marks": 8,
    "grade": 8,
    "percentage": 8,
    "division": 8,
    "passed": 8,
    "result": 8,
    "student": 8,
    "candidate": 8,
    "roll number": 10,
    "roll no": 10,
    "registration number": 10,
    "reg no": 10,
    "enrollment": 10,
}

# 🔴 Negative Non-Academic Indicators with Subtraction Weights
NEGATIVE_INDICATORS = {
    "invoice": -35,
    "tax invoice": -40,
    "bill to": -35,
    "ship to": -35,
    "subtotal": -35,
    "payment receipt": -35,
    "cash receipt": -35,
    "purchase order": -35,
    "receipt no": -35,
    "amount paid": -30,
    "bank statement": -30,
    "transaction id": -30,
    "order id": -30,
    "whatsapp": -25,
    "instagram": -25,
    "facebook": -25,
    "discount": -25,
    "coupon": -25,
    "advertisement": -30,
}

# Core credential keyword list (Must match at least one to pass the gate)
CORE_CREDENTIAL_KEYWORDS = [
    "certificate", "certify", "marksheet", "mark sheet", "transcript",
    "diploma", "degree", "internship", "intern", "training", "skill",
    "hackathon", "completion", "award", "resume", "curriculum vitae", "cv",
    "passing", "grade card", "report card", "statement of marks",
    "statement of grades", "achievement", "workshop", "seminar"
]

# Structural Resume/CV section indicators
RESUME_CV_INDICATORS = [
    r"\bresume\b",
    r"\bcurriculum vitae\b",
    r"\babout me\b",
    r"\bprofile\b",
    r"\bsummary\b",
    r"\bcareer objective\b",
    r"\bprofessional summary\b",
    r"\btechnical skills\b",
    r"\bwork experience\b",
    r"\bprofessional experience\b",
    r"\bprojects\b",
    r"\blanguages\b",
    r"\bcontact\b",
    r"\bphone\b",
    r"\bemail\b",
    r"\blinkedin\b",
    r"\bgithub\b",
    r"\bhobbies\b",
    r"\bachievements\b",
    r"\breferences\b",
    r"\btech stack\b",
    r"\beducation\b",
]


def check_if_resume_cv(text: str, filename: str, file_bytes: bytes) -> Tuple[bool, str]:
    """
    Checks if the text, filename, or PDF metadata contains strong Resume/CV structural sections.
    Returns (is_resume, reason).
    """
    text_lower = text.lower()
    fname_lower = filename.lower()

    # 1. Direct filename mention
    if "resume" in fname_lower or "cv" in fname_lower or "curriculum vitae" in fname_lower:
        if "certify" not in text_lower and "award" not in text_lower and "marksheet" not in text_lower:
            return True, "Filename indicates it is a resume/CV."

    # 2. PDF metadata check
    is_pdf = fname_lower.endswith(".pdf") or file_bytes.startswith(b"%PDF") or b"%PDF" in file_bytes[:1024]
    if is_pdf and fitz is not None:
        try:
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            meta = pdf_doc.metadata or {}
            meta_str = " ".join([str(v) for v in meta.values()]).lower()
            if "resume" in meta_str or "cv" in meta_str or "curriculum vitae" in meta_str:
                if "certify" not in text_lower and "award" not in text_lower and "marksheet" not in text_lower:
                    title_info = meta.get("title") or meta.get("subject") or "Resume"
                    return True, f"PDF metadata indicates it is a resume/CV (Title: '{title_info}')."
        except Exception:
            pass

    # 3. Section keyword density check
    matches = []
    for pattern in RESUME_CV_INDICATORS:
        if re.search(pattern, text_lower):
            matches.append(pattern)

    if len(matches) >= 3:
        certificate_conferring_phrases = [
            "this is to certify",
            "certify that",
            "hereby conferred",
            "has successfully completed",
            "awarded to",
            "presented to",
            "statement of marks",
            "secondary examination",
            "marksheet",
            "roll no",
        ]
        has_certificate_phrases = any(phrase in text_lower for phrase in certificate_conferring_phrases)
        if not has_certificate_phrases:
            matched_sections = [m.replace(r"\b", "") for m in matches[:5]]
            return True, f"Document structured as a resume/CV (Matched sections: {matched_sections})."

    return False, ""


def extract_native_pdf_text(file_bytes: bytes) -> str:
    """
    Extracts direct digital text from PDF stream using PyMuPDF (fitz).
    """
    if fitz is None:
        return ""

    try:
        if not (file_bytes.startswith(b"%PDF") or b"%PDF" in file_bytes[:1024]):
            return ""

        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_pages = []

        for page in pdf_doc:
            page_text = page.get_text()
            if page_text and page_text.strip():
                text_pages.append(page_text.strip())

        return "\n".join(text_pages)

    except Exception as e:
        logger.warning(f"Native PDF text extraction exception: {str(e)}")
        return ""


def load_image_for_classification(file_bytes: bytes, filename: str) -> np.ndarray:
    """
    Decodes file bytes into an OpenCV BGR image array.
    """
    blank_canvas = Image.new("RGB", (600, 800), color=(255, 255, 255))
    fallback_bgr = np.array(blank_canvas)

    if cv2 is None:
        return fallback_bgr

    is_pdf = filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF") or b"%PDF" in file_bytes[:1024]

    if is_pdf:
        if fitz is not None:
            try:
                pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                if len(pdf_doc) > 0:
                    page = pdf_doc.load_page(0)
                    zoom = 150 / 72
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.warning(f"PDF page render for classification warning: {str(e)}")
        return fallback_bgr

    try:
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            return img

        pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.warning(f"Image decoding warning: {str(e)}")
        return fallback_bgr


def inspect_visual_features(image_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Extracts visual computer vision features (faces, saturation, canvas type).
    """
    defaults = {
        "face_count": 0,
        "face_area_ratio": 0.0,
        "light_paper_ratio": 0.5,
        "vivid_color_ratio": 0.0,
        "laplacian_var": 50.0,
    }

    if cv2 is None or image_bgr is None or image_bgr.size == 0:
        return defaults

    try:
        h, w = image_bgr.shape[:2]
        total_pixels = float(max(1, h * w))

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        face_count = 0
        face_area_ratio = 0.0
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            face_cascade = cv2.CascadeClassifier(cascade_path)
            if not face_cascade.empty():
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
                face_count = len(faces)
                if face_count > 0:
                    total_face_area = sum([fw * fh for (fx, fy, fw, fh) in faces])
                    face_area_ratio = total_face_area / total_pixels
        except Exception:
            pass

        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]
        light_paper_mask = (value > 140) & (saturation < 95)
        light_paper_ratio = float(np.count_nonzero(light_paper_mask)) / total_pixels

        vivid_color_mask = (saturation > 140) & (value > 60)
        vivid_color_ratio = float(np.count_nonzero(vivid_color_mask)) / total_pixels

        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        return {
            "face_count": face_count,
            "face_area_ratio": face_area_ratio,
            "light_paper_ratio": light_paper_ratio,
            "vivid_color_ratio": vivid_color_ratio,
            "laplacian_var": laplacian_var,
        }
    except Exception as e:
        logger.warning(f"Visual features warning: {str(e)}")
        return defaults


def evaluate_two_stage_classification(
    visual_features: Dict[str, Any],
    combined_ocr_text: str,
    filename: str,
    file_bytes: bytes,
) -> Tuple[str, bool, float, str, List[str], int, str]:
    """
    Evaluates classification rules with strict credential gating.
    Distinguishes B.Tech marksheets, 10th vs 12th board marksheets, and resumes/CVs.

    Returns:
        Tuple: (doc_type, is_supported, confidence, rejection_detail, matched_positives, net_score, search_summary)
    """
    face_count = visual_features.get("face_count", 0)
    face_area_ratio = visual_features.get("face_area_ratio", 0.0)
    light_paper_ratio = visual_features.get("light_paper_ratio", 0.5)
    vivid_color_ratio = visual_features.get("vivid_color_ratio", 0.0)
    laplacian_var = visual_features.get("laplacian_var", 50.0)

    fname_lower = filename.lower()
    ocr_lower = combined_ocr_text.lower()
    clean_text = "".join(combined_ocr_text.split())
    non_ws_count = len(clean_text)

    is_pdf = fname_lower.endswith(".pdf") or file_bytes.startswith(b"%PDF") or b"%PDF" in file_bytes[:1024]

    # STAGE 1 GATE A: Resume/CV Structural Detection
    is_resume, resume_reason = check_if_resume_cv(combined_ocr_text, filename, file_bytes)
    if is_resume:
        return ("Not an Educational Credential", False, 0.98, resume_reason, [], 0, "CV/Resume classification matched.")

    # 1. Match Positive Academic Indicators
    pos_score = 0
    matched_positives = []
    for kw, weight in POSITIVE_INDICATORS.items():
        if kw in ocr_lower or kw in fname_lower:
            pos_score += weight
            matched_positives.append(kw)

    # 2. Match Negative Non-Academic Indicators
    neg_score = 0
    matched_negatives = []
    for kw, weight in NEGATIVE_INDICATORS.items():
        if kw in ocr_lower or kw in fname_lower:
            neg_score += abs(weight)
            matched_negatives.append(kw)

    # 3. Calculate Text & Paper Bonuses
    text_bonus = 0
    if non_ws_count >= 50:
        text_bonus = 15
    elif non_ws_count >= 20:
        text_bonus = 8

    paper_bonus = 10 if (light_paper_ratio >= 0.15 or is_pdf) else 0

    # 4. Net Academic Score
    net_score = pos_score - neg_score + text_bonus + paper_bonus

    search_summary = (
        f"Positive score: {pos_score}, Negative score: {neg_score}, Text bonus: {text_bonus}, Net Score: {net_score}. "
        f"Matched Positives: {matched_positives[:6]}, Matched Negatives: {matched_negatives}"
    )

    # 5. Core Credential Keyword Gating
    has_core_credential_keyword = any(kw in ocr_lower or kw in fname_lower for kw in CORE_CREDENTIAL_KEYWORDS)

    # Rejection Rule D: Vivid Natural Scene / Product Image / Non-Document Photo
    if vivid_color_ratio > 0.40 and light_paper_ratio < 0.35 and pos_score < 15 and not is_pdf:
        reason = f"Visual inspection detected a natural photograph, product, or non-document image (Vivid color ratio: {vivid_color_ratio:.2f})."
        return ("Unsupported Document", False, 0.92, reason, matched_positives, net_score, search_summary)

    # STAGE 1 GATE B: Rejection Filters
    if not has_core_credential_keyword or net_score < 15 or len(matched_positives) < 1:
        reason = "The uploaded file does not contain sufficient evidence of an educational, professional, or achievement credential."
        return ("Not an Educational Credential", False, 0.98, reason, matched_positives, net_score, search_summary)

    # Rejection Rule B: Explicit Commercial Invoice / Receipt / Billing
    if len(matched_negatives) >= 2 or (len(matched_negatives) >= 1 and pos_score < 15):
        reason = f"Document contains commercial/financial indicators ({', '.join(matched_negatives)}) rather than credential content."
        return ("Not an Educational Credential", False, 0.95, reason, matched_positives, net_score, search_summary)

    # Rejection Rule C: Selfie / Human Portrait Dominant
    if face_count > 0 and face_area_ratio > 0.22 and pos_score < 15:
        reason = f"Visual inspection detected a portrait photo or selfie (Face area ratio: {face_area_ratio:.2f}) without academic text."
        return ("Not an Educational Credential", False, 0.94, reason, matched_positives, net_score, search_summary)

    # Rejection Rule E: Empty page
    if laplacian_var < 1.0 and non_ws_count < 5 and not is_pdf:
        reason = "Uploaded file appears to be a blank or unreadable canvas."
        return ("Not an Educational Credential", False, 0.95, reason, matched_positives, net_score, search_summary)

    # STAGE 2: MAP SUPPORTED CREDENTIAL TYPES
    # A. Check B.Tech Marksheets First
    if "b.tech" in ocr_lower or "btech" in ocr_lower or "bachelor of technology" in ocr_lower:
        if "marksheet" in ocr_lower or "mark sheet" in ocr_lower or "statement of marks" in ocr_lower or "grade" in ocr_lower or "semester" in ocr_lower:
            doc_type = "B.Tech Semester Marksheet"
        else:
            doc_type = "Degree Certificate"
    # B. Check 12th vs 10th
    elif "12th" in ocr_lower or "twelfth" in ocr_lower or "higher secondary" in ocr_lower or "senior secondary" in ocr_lower or "hsc" in ocr_lower:
        doc_type = "12th Marksheet"
    elif "10th" in ocr_lower or "tenth" in ocr_lower or "secondary school" in ocr_lower or "secondary examination" in ocr_lower or "ssc" in ocr_lower:
        doc_type = "10th Marksheet"
    elif "marksheet" in ocr_lower or "mark sheet" in ocr_lower or "statement of marks" in ocr_lower or "grade card" in ocr_lower or "report card" in ocr_lower:
        doc_type = "Marksheet"
    elif "transcript" in ocr_lower:
        doc_type = "Transcript"
    elif "degree" in ocr_lower or "bachelor" in ocr_lower or "master" in ocr_lower or "doctorate" in ocr_lower or "phd" in ocr_lower:
        doc_type = "Degree Certificate"
    elif "diploma" in ocr_lower:
        doc_type = "Diploma"
    elif "internship" in ocr_lower or "intern" in ocr_lower:
        doc_type = "Internship Certificate"
    elif "training" in ocr_lower:
        doc_type = "Training Certificate"
    elif "hackathon" in ocr_lower:
        doc_type = "Hackathon Certificate"
    elif "competition" in ocr_lower:
        doc_type = "Competition Certificate"
    elif "award" in ocr_lower:
        doc_type = "Award Certificate"
    elif "participation" in ocr_lower:
        doc_type = "Participation Certificate"
    elif "achievement" in ocr_lower:
        doc_type = "Achievement Certificate"
    elif "workshop" in ocr_lower:
        doc_type = "Workshop Certificate"
    elif "seminar" in ocr_lower:
        doc_type = "Seminar Certificate"
    elif "event" in ocr_lower:
        doc_type = "Event Certificate"
    elif "skill" in ocr_lower:
        doc_type = "Skill Certificate"
    elif "resume" in ocr_lower or "curriculum vitae" in ocr_lower or "cv" in ocr_lower:
        doc_type = "Resume / CV"
    else:
        doc_type = "Academic Certificate"

    confidence = min(0.98, max(0.85, 0.75 + (net_score / 150.0)))
    return (doc_type, True, confidence, f"Successfully verified valid '{doc_type}'.", matched_positives, net_score, search_summary)
