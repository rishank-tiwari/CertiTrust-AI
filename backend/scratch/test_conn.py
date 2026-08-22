import urllib.request
import urllib.error
import json

def test_endpoint(url):
    print(f"Testing {url}...")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode()
            print(f"Success! Status: {status}")
            try:
                print(json.loads(body))
            except Exception:
                print(body[:200])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode()[:200])
    except Exception as e:
        print(f"Error: {e}")

test_endpoint("http://[::1]:8000/health")
test_endpoint("http://[::1]:8000/")
test_endpoint("http://[::1]:8000/auth/me")
test_endpoint("http://[::1]:8000/employer/verification-history")
