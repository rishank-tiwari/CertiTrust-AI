import urllib.request
import urllib.error
import json
import io

def run_test():
    base_url = "http://[::1]:8000"
    
    # -------------------------------------------------------------
    # 1. Sign up Issuer and Employer and Student
    # -------------------------------------------------------------
    print("1. Creating Accounts...")
    tokens = {}
    
    for name, email, role in [
        ("Tech University", "issuer@uni.edu", "institution"),
        ("Global Corp", "employer@corp.com", "employer"),
        ("Rishank Tiwari", "2503031460770@paruluniversity.ac.in", "student")
    ]:
        signup_payload = {
            "full_name": name,
            "email": email,
            "password": "securepassword",
            "role": role,
            "organization": name if role != "student" else "Parul University"
        }
        req = urllib.request.Request(f"{base_url}/auth/signup", data=json.dumps(signup_payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"   Created {role}: {email}")
        except urllib.error.HTTPError as e:
            if e.code == 400: # Email already exists
                print(f"   {role} '{email}' already exists.")
            else:
                print(f"   Signup failed: {e.code} - {e.read().decode()}")
                return
                
        # Login
        login_payload = {"email": email, "password": "securepassword"}
        req = urllib.request.Request(f"{base_url}/auth/login", data=json.dumps(login_payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            tokens[role] = data["access_token"]
            
    # -------------------------------------------------------------
    # 2. Issuer Uploads/Registers a Credential (B.Tech in CS)
    # -------------------------------------------------------------
    print("\n2. Issuer Registers Certificate...")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    # Construct multipart/form-data payload
    form_fields = {
        "student_name": "Rishank Tiwari",
        "student_email": "2503031460770@paruluniversity.ac.in",
        "university": "Parul University",
        "degree": "B.Tech",
        "course": "Computer Science",
        "certificate_number": "CERT-2026-001"
    }
    
    body = io.BytesIO()
    for name, value in form_fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(f"{value}\r\n".encode())
        
    # File field
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="parul_cert.png"\r\n'.encode())
    body.write(b"Content-Type: image/png\r\n\r\n")
    body.write(b"fake_file_content_representing_certificate_image")
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    
    payload_data = body.getvalue()
    
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {tokens['institution']}"
    }
    
    req = urllib.request.Request(f"{base_url}/institution/certificates", data=payload_data, headers=headers, method="POST")
    cert_id = ""
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            cert_id = data["id"]
            print(f"   Registered Certificate successfully. ID: {cert_id}")
            print(data)
    except urllib.error.HTTPError as e:
        print(f"   Institution upload failed: {e.code} - {e.read().decode()}")
        return

    # -------------------------------------------------------------
    # 3. Trigger Analysis to change status from pending to verified
    # -------------------------------------------------------------
    print("\n3. Triggering AI Analysis on Registered Certificate...")
    analyze_payload = {"certificate_id": cert_id}
    req = urllib.request.Request(f"{base_url}/analyze", data=json.dumps(analyze_payload).encode(), headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tokens['institution']}"
    }, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("   Analysis Successful!")
            print(data)
    except urllib.error.HTTPError as e:
        print(f"   Analysis failed: {e.code} - {e.read().decode()}")
        return

    # -------------------------------------------------------------
    # 4. Employer Verifies the Certificate (Should match source of truth)
    # -------------------------------------------------------------
    print("\n4. Employer Verifies Certificate...")
    # Multipart body containing same file bytes and certificate number in extracted mock details
    # In live system, AI parses certificate details. For test, we verify the matching logic
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="submitted_cert.png"\r\n'.encode())
    body.write(b"Content-Type: image/png\r\n\r\n")
    body.write(b"fake_file_content_representing_certificate_image") # Same content matches file_hash!
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {tokens['employer']}"
    }
    
    req = urllib.request.Request(f"{base_url}/employer/verify-certificate", data=body.getvalue(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("   Verification Response:")
            print(data)
    except urllib.error.HTTPError as e:
        print(f"   Employer verification failed: {e.code} - {e.read().decode()}")
        return

    # -------------------------------------------------------------
    # 5. Employer Uploads a Resume for Verification (Real AI Resume Analysis)
    # -------------------------------------------------------------
    print("\n5. Employer Analyzes Resume (Real Resume Intelligence)...")
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(f'Content-Disposition: form-data; name="file"; filename="resume.txt"\r\n'.encode())
    body.write(b"Content-Type: text/plain\r\n\r\n")
    body.write(b"Rishank Tiwari\nEmail: 2503031460770@paruluniversity.ac.in\nSkills: Python, React, JavaScript, Linear Algebra\nEducation: B.Tech in Computer Science\nGithub link: https://github.com/rishank/myproject")
    body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    
    req = urllib.request.Request(f"{base_url}/employer/verify-resume", data=body.getvalue(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print("   Resume Analysis Results:")
            print(data)
    except urllib.error.HTTPError as e:
        print(f"   Resume Verification failed: {e.code} - {e.read().decode()}")
        return

run_test()
