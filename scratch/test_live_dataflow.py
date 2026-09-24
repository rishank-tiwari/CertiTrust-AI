import requests

BASE_URL = "https://certitrust-platform.vercel.app"

def test_live():
    print("=== TESTING LIVE PRODUCTION API DATAFLOW ===")
    
    # 1. Health check
    res_health = requests.get(f"{BASE_URL}/api/health")
    print("GET /api/health:", res_health.status_code, res_health.json())

    # 2. Signup / Login as institution
    login_payload = {
        "email": "institution_test@certitrust.ai",
        "password": "TestPassword123!"
    }
    
    # Try login first
    res_login = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    if res_login.status_code != 200:
        print("Login failed, attempting signup...")
        signup_payload = {
            "full_name": "Test Institution",
            "email": "institution_test@certitrust.ai",
            "password": "TestPassword123!",
            "role": "institution",
            "organization": "Test University"
        }
        res_signup = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload)
        print("POST /api/auth/signup:", res_signup.status_code, res_signup.text)
        res_login = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        
    print("POST /api/auth/login:", res_login.status_code, res_login.json())
    token = res_login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 3. GET /api/auth/me
    res_me = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print("GET /api/auth/me:", res_me.status_code, res_me.json())
    user_info = res_me.json()
    user_id = user_info.get("id")

    # 4. GET /api/institution/credentials before creation
    res_creds_before = requests.get(f"{BASE_URL}/api/institution/credentials", headers=headers)
    print("GET /api/institution/credentials (before):", res_creds_before.status_code, res_creds_before.json())

    # 5. Create / Upload a credential via POST /api/institution/certificates
    dummy_file = ("test_cert.pdf", b"%PDF-1.4 sample certificate content", "application/pdf")
    data = {
        "student_name": "Test Student",
        "student_email": "student@example.com",
        "university": "Test University",
        "degree": "Bachelor of Science",
        "course": "Computer Science",
        "certificate_number": "CERT-LIVE-TEST-001"
    }
    files = {"file": dummy_file}
    res_create = requests.post(f"{BASE_URL}/api/institution/certificates", headers=headers, data=data, files=files)
    print("POST /api/institution/certificates:", res_create.status_code, res_create.json())

    # 6. GET /api/institution/credentials after creation
    res_creds_after = requests.get(f"{BASE_URL}/api/institution/credentials", headers=headers)
    print("GET /api/institution/credentials (after):", res_creds_after.status_code, res_creds_after.json())

if __name__ == "__main__":
    test_live()
