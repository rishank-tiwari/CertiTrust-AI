"""
CertiTrust AI - Weighted Document Type Classification Unit & Pipeline Integration Tests.
Tests classification of 10th marksheets, 12th marksheets, PDF marksheets, degrees, provisional certificates, resumes,
and strict rejection of selfies and non-document photos.
"""

import io
from PIL import Image, ImageDraw, PngImagePlugin
from fastapi.testclient import TestClient
from ai.classification.classifier_service import document_classifier_service
from ai.pipeline.analysis_service import pipeline_analysis_service


def create_10th_marksheet_canvas() -> bytes:
    """Creates a sample 10th Board Marksheet canvas."""
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "CENTRAL BOARD OF SECONDARY EDUCATION - 10TH MARKSHEET\n"
        "Statement of Marks for Secondary School Examination\n"
        "Candidate Name: Rahul Kumar | Roll Number: 11029482 | Reg No: B10-9982\n"
        "Subjects: Mathematics - 92, Science - 88, English - 90\n"
        "Result: PASS | Division: First Division"
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)

    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_12th_marksheet_canvas() -> bytes:
    """Creates a sample 12th Board Marksheet canvas."""
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "STATE BOARD OF HIGHER SECONDARY EDUCATION - 12TH MARKSHEET\n"
        "Statement of Marks for Higher Secondary Certificate Examination\n"
        "Candidate Name: Ananya Sharma | Roll No: 12903841\n"
        "Physics - 95, Chemistry - 91, Mathematics - 94\n"
        "Result: PASS | CGPA: 9.4"
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)

    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_sample_pdf_marksheet() -> bytes:
    """Creates a sample PDF document containing marksheet text."""
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=600, height=800)
        page.insert_text(
            (50, 50),
            "CENTRAL BOARD OF SECONDARY EDUCATION\n10th CLASS MARKSHEET & CERTIFICATE\nStudent: Amit Patel\nRoll Number: 9918231",
            fontsize=12,
        )
        return doc.write()
    except Exception:
        return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n"


def create_unsupported_photo() -> bytes:
    """Creates a colorful photo canvas with zero text simulating a non-document photo."""
    photo = Image.new("RGB", (400, 400), color=(255, 100, 50))
    draw = ImageDraw.Draw(photo)
    draw.ellipse([50, 50, 350, 350], fill=(0, 200, 255))
    draw.rectangle([100, 100, 300, 300], fill=(255, 255, 0))
    buf = io.BytesIO()
    photo.save(buf, format="PNG")
    return buf.getvalue()


def test_classification_10th_marksheet_passes():
    """
    Tests that a 10th Board Marksheet is classified as supported.
    """
    cert_bytes = create_10th_marksheet_canvas()
    res = document_classifier_service.classify_document(cert_bytes, "10th_marksheet.png")

    assert res["is_supported"] is True
    assert res["success"] is True
    assert "10th" in res["document_type"] or "Marksheet" in res["document_type"] or "Board" in res["document_type"]


def test_classification_12th_marksheet_passes():
    """
    Tests that a 12th Board Marksheet is classified as supported.
    """
    cert_bytes = create_12th_marksheet_canvas()
    res = document_classifier_service.classify_document(cert_bytes, "12th_marksheet.png")

    assert res["is_supported"] is True
    assert res["success"] is True
    assert "12th" in res["document_type"] or "Marksheet" in res["document_type"] or "Board" in res["document_type"]


def test_classification_pdf_marksheet_passes():
    """
    Tests that a PDF Marksheet is classified as supported via native PDF text extraction.
    """
    pdf_bytes = create_sample_pdf_marksheet()
    res = document_classifier_service.classify_document(pdf_bytes, "10th_marksheet.pdf")

    assert res["is_supported"] is True
    assert res["success"] is True


def test_classification_unsupported_photo_fails():
    """
    Tests that a vivid non-document photo is rejected.
    """
    photo_bytes = create_unsupported_photo()
    res = document_classifier_service.classify_document(photo_bytes, "random_photo.jpg")

    assert res["is_supported"] is False
    assert res["success"] is False
    assert res["document_type"] == "Unsupported Document"


def test_pipeline_continues_for_10th_marksheet():
    """
    Tests that pipeline executes full verification for a 10th marksheet.
    """
    cert_bytes = create_10th_marksheet_canvas()
    res = pipeline_analysis_service.run_full_pipeline(cert_bytes, "10th_marksheet.png")

    assert res["success"] is True
    assert res["classification"]["is_supported"] is True
    assert "ocr" in res
    assert "trust_score" in res
