import unittest
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime, timezone
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from database import get_database, connect_db

class TestFraudDetection(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    async def asyncSetUp(self):
        await connect_db()
        self.db = get_database()
        
        # Create student and employer accounts
        self.student_doc = {
            "email": "rishank@test.com",
            "full_name": "Rishank Tiwari",
            "role": "student",
            "password": "hashed_password"
        }
        await self.db.users.insert_one(self.student_doc)
        
        self.employer_doc = {
            "email": "employer@corp.com",
            "full_name": "Verify Corp",
            "role": "employer",
            "password": "hashed_password"
        }
        await self.db.users.insert_one(self.employer_doc)

        # Override dependency
        from middleware.auth_middleware import get_current_user
        app.dependency_overrides[get_current_user] = lambda: self.employer_doc
        
        # Issuer registered certificate
        self.registered_certificate = {
            "student_name": "Rishank Tiwari",
            "student_email": "rishank@test.com",
            "university": "Verification University",
            "degree": "B.Tech",
            "course": "Computer Science",
            "certificate_number": "CERT-2026-999",
            "file_hash": "original_hash_value_A",
            "cgpa": "6.70",
            "status": "verified",
            "created_at": datetime.now(timezone.utc)
        }
        res = await self.db.credentials.insert_one(self.registered_certificate)
        self.registered_certificate["_id"] = res.inserted_id

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        
    @patch('services.ai_service.analyze_certificate')
    @patch('services.blockchain_service.store_on_blockchain')
    async def test_all_scenarios(self, mock_store, mock_analyze):
        # 1. Setup mocks
        mock_store.return_value = {"tx_hash": "mock_tx_hash", "status": "confirmed"}
        
        # -----------------------------------------------------------------
        # TEST 1: Exact registered marksheet (matches hash and all fields)
        # -----------------------------------------------------------------
        mock_analyze.return_value = {
            "authenticity_score": 90,
            "risk_level": "low",
            "fraud_flags": [],
            "extracted_data": {
                "student_name": "Rishank Tiwari",
                "university": "Verification University",
                "degree": "B.Tech",
                "certificate_number": "CERT-2026-999",
                "cgpa": "6.70"
            }
        }
        
        # Mock file upload
        file_data = {"file": ("original_cert.png", b"file_contents_A", "image/png")}
        response = self.client.post("/employer/verify-certificate", files=file_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("\n[TEST 1 RESULT]")
        print(f"Status: {data['status']}")
        print(f"Trust Signals: {data['trust_signals']}")
        
        # Fraud flags must pass
        fraud_sig = [s for s in data["trust_signals"] if s["check"] == "Fraud flags"][0]
        self.assertEqual(fraud_sig["result"], "pass")
        self.assertEqual(data["status"], "verified")

        # -----------------------------------------------------------------
        # TEST 2: Scanned/genuine copy (different hash, same values)
        # -----------------------------------------------------------------
        # Uploading b"file_contents_B" -> different file hash
        # Mock extracted data matches issuer record
        mock_analyze.return_value = {
            "authenticity_score": 90,
            "risk_level": "low",
            "fraud_flags": [],
            "extracted_data": {
                "student_name": "Rishank Tiwari",
                "university": "Verification University",
                "degree": "B.Tech",
                "certificate_number": "CERT-2026-999",
                "cgpa": "6.70"
            }
        }
        
        file_data = {"file": ("scanned_cert.png", b"file_contents_B", "image/png")}
        response = self.client.post("/employer/verify-certificate", files=file_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("\n[TEST 2 RESULT]")
        print(f"Status: {data['status']}")
        print(f"Message: {data.get('message')}")
        
        fraud_sig = [s for s in data["trust_signals"] if s["check"] == "Fraud flags"][0]
        self.assertEqual(fraud_sig["result"], "pass")
        self.assertEqual(data["status"], "verified")
        self.assertEqual(data.get("message"), "File hash differs, but the credential content matches the issuer's trusted record.")

        # -----------------------------------------------------------------
        # TEST 3: Modified CGPA (6.70 -> 8.70)
        # -----------------------------------------------------------------
        mock_analyze.return_value = {
            "authenticity_score": 90,
            "risk_level": "low",
            "fraud_flags": [],
            "extracted_data": {
                "student_name": "Rishank Tiwari",
                "university": "Verification University",
                "degree": "B.Tech",
                "certificate_number": "CERT-2026-999",
                "cgpa": "8.70" # CHANGED CGPA
            }
        }
        
        file_data = {"file": ("modified_cgpa.png", b"file_contents_B", "image/png")}
        response = self.client.post("/employer/verify-certificate", files=file_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("\n[TEST 3 RESULT]")
        print(f"Status: {data['status']}")
        
        # Verify document is flagged
        self.assertEqual(data["status"], "flagged")
        fraud_sig = [s for s in data["trust_signals"] if s["check"] == "Fraud flags"][0]
        self.assertEqual(fraud_sig["result"], "fail")
        
        # Verify in database that verification_doc has correct fraud flags & changed parameters
        db_rec = await self.db.verification_records.find_one({"status": "flagged"})
        self.assertIsNotNone(db_rec)
        print("Fraud flags in DB:", db_rec["fraud_flags"])
        print("Changed parameters in DB:", db_rec["changed_parameters"])
        
        self.assertEqual(db_rec["fraud_flags"]["status"], "FAIL")
        self.assertEqual(db_rec["changed_parameters"][0]["field"], "cgpa")
        self.assertEqual(float(db_rec["changed_parameters"][0]["original_value"]), 6.70)
        self.assertEqual(float(db_rec["changed_parameters"][0]["submitted_value"]), 8.70)
        self.assertEqual(db_rec["changed_parameters"][0]["status"], "CHANGED")
        self.assertEqual(db_rec["changed_parameters"][0]["severity"], "CRITICAL")

        # -----------------------------------------------------------------
        # TEST 4: Modified Roll Number (CERT-2026-999 -> CERT-2026-888)
        # -----------------------------------------------------------------
        # Because certificate number is changed, it won't match direct lookup,
        # but it will fall back to student name matching ("Rishank Tiwari"),
        # and then discover the mismatch on certificate_number!
        mock_analyze.return_value = {
            "authenticity_score": 90,
            "risk_level": "low",
            "fraud_flags": [],
            "extracted_data": {
                "student_name": "Rishank Tiwari",
                "university": "Verification University",
                "degree": "B.Tech",
                "certificate_number": "CERT-2026-888", # CHANGED ROLL NUMBER
                "cgpa": "6.70"
            }
        }
        
        file_data = {"file": ("modified_roll.png", b"file_contents_B", "image/png")}
        response = self.client.post("/employer/verify-certificate", files=file_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("\n[TEST 4 RESULT]")
        print(f"Status: {data['status']}")
        self.assertEqual(data["status"], "flagged")
        fraud_sig = [s for s in data["trust_signals"] if s["check"] == "Fraud flags"][0]
        self.assertEqual(fraud_sig["result"], "fail")

        # -----------------------------------------------------------------
        # TEST 5: Modified Student Name (Rishank Tiwari -> Rahul Tiwari)
        # -----------------------------------------------------------------
        # Matches by certificate number CERT-2026-999, then checks fields
        mock_analyze.return_value = {
            "authenticity_score": 90,
            "risk_level": "low",
            "fraud_flags": [],
            "extracted_data": {
                "student_name": "Rahul Tiwari", # CHANGED NAME
                "university": "Verification University",
                "degree": "B.Tech",
                "certificate_number": "CERT-2026-999",
                "cgpa": "6.70"
            }
        }
        
        file_data = {"file": ("modified_name.png", b"file_contents_B", "image/png")}
        response = self.client.post("/employer/verify-certificate", files=file_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("\n[TEST 5 RESULT]")
        print(f"Status: {data['status']}")
        self.assertEqual(data["status"], "flagged")
        fraud_sig = [s for s in data["trust_signals"] if s["check"] == "Fraud flags"][0]
        self.assertEqual(fraud_sig["result"], "fail")

        # -----------------------------------------------------------------
        # TEST 6: Upload unrelated/random document (AI Classifier Rejects)
        # -----------------------------------------------------------------
        # In real life, classify_document returns "Not an Educational Credential"
        # and authenticity score 0. Let's verify status is not_verified/flagged
        mock_analyze.return_value = {
            "authenticity_score": 0,
            "risk_level": "high",
            "fraud_flags": [],
            "extracted_data": {
                "student_name": "Unknown Student",
                "university": "Not Found",
                "degree": "Certificate",
                "certificate_number": "N/A"
            }
        }
        
        file_data = {"file": ("random.png", b"file_contents_C", "image/png")}
        response = self.client.post("/employer/verify-certificate", files=file_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        print("\n[TEST 6 RESULT]")
        print(f"Status: {data['status']}")
        self.assertEqual(data["status"], "not_verified")
        
        print("\nAll 6 verification tests passed successfully!")

if __name__ == '__main__':
    unittest.main()
