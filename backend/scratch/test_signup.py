import urllib.request
import urllib.error
import json

def run_signup_test():
    url = "http://[::1]:8000/auth/signup"
    payload = {
        "full_name": "Rishank Tiwari",
        "email": "2503031460770@paruluniversity.ac.in",
        "password": "my_secure_password",
        "role": "institution",
        "organization": "Parul Institute of Engineering and Technology"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode()
            print(f"Signup Success! Status: {status}")
            print(json.loads(body))
    except urllib.error.HTTPError as e:
        print(f"Signup HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
    except Exception as e:
        print(f"Signup Error: {e}")

run_signup_test()
