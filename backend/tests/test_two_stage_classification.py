"""
CertiTrust AI - Comprehensive Two-Stage Classification Test Suite.
Tests all user-requested document categories:
1. Genuine Academic Certificate
2. Marksheet / Board Certificate
3. Resume / CV
4. Commercial Invoice / Receipt (Rejected)
5. Selfie / Portrait Photo (Rejected)
"""

import io
from PIL import Image, ImageDraw, PngImagePlugin
from fastapi.testclient import TestClient
from app.main import app


def create_academic_certificate_png() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "STANFORD UNIVERSITY OFFICIAL DEGREE CERTIFICATE\n"
        "This is to certify that Student Name: Jane Doe has successfully completed\n"
        "the requirements for the degree of Bachelor of Technology in Computer Science.\n"
        "Registration Number: CT-998241 | Issued Date: 2026-05-10 | CGPA: 3.85\n"
        "Signed by the Board of Directors and University Controller."
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_10th_marksheet_png() -> bytes:
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


def create_resume_cv_png() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=3)
    text_content = (
        "CURRICULUM VITAE - RESUME\n"
        "Name: Alex Mercer | Email: alex@example.com\n"
        "Education: Bachelor of Computer Science, University of Technology\n"
        "Skills: Python, Machine Learning, FastAPI, PostgreSQL\n"
        "Academic Projects: Machine Learning Verification Engine"
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_commercial_invoice_png() -> bytes:
    cert = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(cert)
    draw.rectangle([20, 20, 780, 580], outline=(0, 0, 0), width=2)
    text_content = (
        "TAX INVOICE - PAYMENT RECEIPT\n"
        "Bill To: John Smith | Order ID: INV-99821\n"
        "Item 1: Laptop Computer - Subtotal: $1,200\n"
        "Tax: $120 | Total Amount Paid: $1,320\n"
        "Thank you for your purchase!"
    )
    draw.text((40, 50), text_content, fill=(0, 0, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", text_content)
    buf = io.BytesIO()
    cert.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


def create_random_photo_png() -> bytes:
    photo = Image.new("RGB", (400, 400), color=(255, 100, 50))
    draw = ImageDraw.Draw(photo)
    draw.ellipse([50, 50, 350, 350], fill=(0, 200, 255))
    draw.rectangle([100, 100, 300, 300], fill=(255, 255, 0))
    buf = io.BytesIO()
    photo.save(buf, format="PNG")
    return buf.getvalue()


def test_all_five_categories():
    client = TestClient(app)

    print("\n==================================================")
    print("TEST 1: Genuine Academic Certificate")
    print("==================================================")
    res1 = client.post("/api/v1/analyze", files={"certificate": ("academic_certificate.png", create_academic_certificate_png(), "image/png")})
    assert res1.status_code == 200
    data1 = res1.json()
    print("API Response 1 (Genuine Academic Certificate):")
    print(f"success: {data1.get('success')}")
    print(f"document_type: {data1.get('classification', {}).get('document_type')}")
    print(f"is_supported: {data1.get('classification', {}).get('is_supported')}")
    print(f"trust_score: {data1.get('trust_score', {}).get('trust_score')}%")
    assert data1["success"] is True
    assert data1["classification"]["is_supported"] is True

    print("\n==================================================")
    print("TEST 2: Marksheet / Board Certificate")
    print("==================================================")
    res2 = client.post("/api/v1/analyze", files={"certificate": ("10th_marksheet.png", create_10th_marksheet_png(), "image/png")})
    assert res2.status_code == 200
    data2 = res2.json()
    print("API Response 2 (Marksheet / Board Certificate):")
    print(f"success: {data2.get('success')}")
    print(f"document_type: {data2.get('classification', {}).get('document_type')}")
    print(f"is_supported: {data2.get('classification', {}).get('is_supported')}")
    assert data2["success"] is True
    assert data2["classification"]["is_supported"] is True

    print("\n==================================================")
    print("TEST 3: Resume / CV")
    print("==================================================")
    res3 = client.post("/api/v1/analyze", files={"certificate": ("resume.png", create_resume_cv_png(), "image/png")})
    assert res3.status_code == 200
    data3 = res3.json()
    print("API Response 3 (Resume / CV):")
    print(f"success: {data3.get('success')}")
    print(f"document_type: {data3.get('classification', {}).get('document_type')}")
    print(f"is_supported: {data3.get('classification', {}).get('is_supported')}")
    assert data3["success"] is True
    assert data3["classification"]["is_supported"] is True

    print("\n==================================================")
    print("TEST 4: Commercial Invoice / Receipt (Rejected)")
    print("==================================================")
    res4 = client.post("/api/v1/analyze", files={"certificate": ("invoice.png", create_commercial_invoice_png(), "image/png")})
    assert res4.status_code == 200
    data4 = res4.json()
    print("API Response 4 (Commercial Invoice / Receipt):")
    print(f"success: {data4.get('success')}")
    print(f"document_type: {data4.get('document_type')}")
    print(f"is_supported: {data4.get('is_supported')}")
    print(f"reason: {data4.get('reason')}")
    assert data4["success"] is False
    assert data4["is_supported"] is False

    print("\n==================================================")
    print("TEST 5: Random Unrelated Photo (Rejected)")
    print("==================================================")
    res5 = client.post("/api/v1/analyze", files={"certificate": ("random_photo.png", create_random_photo_png(), "image/png")})
    assert res5.status_code == 200
    data5 = res5.json()
    print("API Response 5 (Random Photo):")
    print(f"success: {data5.get('success')}")
    print(f"document_type: {data5.get('document_type')}")
    print(f"is_supported: {data5.get('is_supported')}")
    print(f"reason: {data5.get('reason')}")
    assert data5["success"] is False
    assert data5["is_supported"] is False

    print("\n==================================================")
    print("ALL 5 CATEGORY TEST SUITES PASSED CLEANLY!")
    print("==================================================")
