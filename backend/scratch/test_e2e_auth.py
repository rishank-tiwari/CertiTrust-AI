import urllib.request
import urllib.error
import json

def run_test():
    base_url = "http://[::1]:8000"
    
    # 1. Signup
    signup_url = f"{base_url}/auth/signup"
    signup_payload = {
        "full_name": "Alex Morgan",
        "email": "alex.morgan@test.com",
        "password": "alexpassword",
        "role": "student",
        "organization": "Test University"
    }
    
    print("Testing Signup...")
    req = urllib.request.Request(signup_url, data=json.dumps(signup_payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode())
            print("Signup Success!")
            print(res_body)
    except urllib.error.HTTPError as e:
        print(f"Signup HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
        return
        
    # 2. Login
    login_url = f"{base_url}/auth/login"
    login_payload = {
        "email": "alex.morgan@test.com",
        "password": "alexpassword"
    }
    
    print("\nTesting Login...")
    req = urllib.request.Request(login_url, data=json.dumps(login_payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    token = ""
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode())
            print("Login Success!")
            print(res_body)
            token = res_body.get("access_token")
    except urllib.error.HTTPError as e:
        print(f"Login HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
        return
        
    # 3. Get profile /me
    me_url = f"{base_url}/auth/me"
    print("\nTesting /auth/me profile fetch...")
    req = urllib.request.Request(me_url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode())
            print("Profile Fetch Success!")
            print(res_body)
    except urllib.error.HTTPError as e:
        print(f"Profile Fetch HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
        return

run_test()
