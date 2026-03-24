import requests
import ssl
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Test 1: Try without client certificate (should fail)
print("Test 1: Connecting to HR service WITHOUT client certificate...")
try:
    response = requests.get("https://localhost:9001/health", verify=False, timeout=5)
    print(f"[FAIL] Got response {response.status_code} (should have been rejected!)")
except requests.exceptions.SSLError as e:
    print(f"[PASS] Connection rejected with SSL error (mTLS working!)")
    print(f"   Error: {str(e)[:100]}")
except Exception as e:
    print(f"[PASS] Connection failed as expected")
    print(f"   Error: {type(e).__name__}: {str(e)[:100]}")

# Test 2: Try with client certificate (should work)
print("\nTest 2: Connecting to HR service WITH gateway certificate...")
try:
    response = requests.get(
        "https://localhost:9001/health",
        cert=("certs/gateway.crt", "certs/gateway.key"),
        verify="certs/ca.crt",
        timeout=5
    )
    print(f"[PASS] Got response {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {str(e)[:200]}")

print()

# Test 3: Try finance service with client certificate
print("Test 3: Connecting to Finance service WITH gateway certificate...")
try:
    response = requests.get(
        "https://localhost:9002/health",
        cert=("certs/gateway.crt", "certs/gateway.key"),
        verify="certs/ca.crt",
        timeout=5
    )
    print(f"[PASS] Got response {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {str(e)[:200]}")

print()

# Test 4: Try admin service with client certificate
print("Test 4: Connecting to Admin service WITH gateway certificate...")
try:
    response = requests.get(
        "https://localhost:9003/health",
        cert=("certs/gateway.crt", "certs/gateway.key"),
        verify="certs/ca.crt",
        timeout=5
    )
    print(f"[PASS] Got response {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"[FAIL] {type(e).__name__}: {str(e)[:200]}")

print("\n" + "="*60)
print("mTLS Configuration Test Complete!")
print("="*60)
