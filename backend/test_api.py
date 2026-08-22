"""Full end-to-end test for CertiTrust AI API"""
import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"


def api_json(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def api_upload(path, fields, filename, file_content, token):
    boundary = "----TestBoundary123456"
    parts = []
    for key, value in fields.items():
        parts.append(f"--{boundary}")
        parts.append(f'Content-Disposition: form-data; name="{key}"')
        parts.append("")
        parts.append(value)

    parts.append(f"--{boundary}")
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    parts.append("Content-Type: application/pdf")
    parts.append("")
    parts.append(file_content)
    parts.append(f"--{boundary}--")
    parts.append("")

    body = "\r\n".join(parts).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def main():
    print("=" * 60)
    print("  CertiTrust AI — Full API Test")
    print("=" * 60)

    # Test 1: Login (user already created)
    print("\n[TEST 1] LOGIN")
    r = api_json("POST", "/auth/login", {
        "email": "admin@delhi-university.edu",
        "password": "hackathon2026"
    })
    print(f"  Status: {'OK' if 'access_token' in r else 'FAILED'}")
    token = r.get("access_token", "")
    if not token:
        print("  ERROR:", r)
        return

    # Test 2: Upload Certificate
    print("\n[TEST 2] UPLOAD CERTIFICATE")
    r = api_upload("/upload", {
        "student_name": "Eshant Bhardwaj",
        "university": "Delhi University",
        "degree": "B.Tech AI & ML",
        "certificate_number": "DU-2026-AI-001",
    }, "degree_certificate.pdf", "Fake PDF content for testing purposes", token)
    print(f"  Status: {'OK' if 'id' in r else 'FAILED'}")
    print(f"  Certificate ID: {r.get('id', 'N/A')}")
    print(f"  File Hash: {r.get('file_hash', 'N/A')[:20]}...")
    print(f"  Status: {r.get('status', 'N/A')}")
    cert_id = r.get("id")
    if not cert_id:
        print("  ERROR:", json.dumps(r, indent=2))
        return

    # Test 3: Analyze Certificate (AI + Blockchain)
    print("\n[TEST 3] ANALYZE CERTIFICATE (AI + Blockchain pipeline)")
    print("  Processing... (simulates AI + blockchain delay)")
    r = api_json("POST", "/analyze", {"certificate_id": cert_id}, token=token)
    print(f"  Status: {'OK' if 'verification' in r else 'FAILED'}")
    if "verification" in r:
        v = r["verification"]
        print(f"  Authenticity Score: {v.get('authenticity_score', 'N/A')}")
        print(f"  Risk Level: {v.get('risk_level', 'N/A')}")
        print(f"  Fraud Flags: {v.get('fraud_flags', [])}")
        print(f"  Final Status: {v.get('status', 'N/A')}")
        b = r.get("blockchain", {})
        print(f"  Blockchain TX: {b.get('tx_hash', 'N/A')[:30]}...")
        print(f"  Network: {b.get('network', 'N/A')}")
        print(f"  Block Number: {b.get('block_number', 'N/A')}")
    else:
        print("  ERROR:", json.dumps(r, indent=2))

    # Test 4: Verify Certificate (Public — no auth)
    print("\n[TEST 4] VERIFY CERTIFICATE (public endpoint)")
    r = api_json("GET", f"/verify/{cert_id}")
    print(f"  Status: {'OK' if 'certificate' in r else 'FAILED'}")
    if "certificate" in r:
        c = r["certificate"]
        print(f"  Student: {c.get('student_name', 'N/A')}")
        print(f"  University: {c.get('university', 'N/A')}")
        print(f"  Degree: {c.get('degree', 'N/A')}")
        print(f"  Verification Status: {r.get('status', 'N/A')}")
    else:
        print("  ERROR:", json.dumps(r, indent=2))

    print("\n" + "=" * 60)
    print("  ALL TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
