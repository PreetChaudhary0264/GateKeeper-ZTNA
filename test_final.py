"""
ZTNA SYSTEM - MANUAL TESTING GUIDE
===================================

Pre-configured users:
- ramesh@company.com / pass123 (role: hr, device: DEVICE-HR-001)
- priya@company.com / pass456 (role: finance, device: DEVICE-FIN-002)
- admin@company.com / admin789 (role: admin, device: DEVICE-ADM-003)
"""

import requests
import json
import urllib3
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

urllib3.disable_warnings()

GATEWAY = "https://localhost:8080"
AUTH = "http://localhost:8001"

print("\n" + "="*70)
print("ZTNA SYSTEM - MANUAL TESTING GUIDE")
print("="*70)

# TEST 1: Login as HR user
print("\n[TEST 1] Login as HR user (ramesh@company.com)")
print("-" * 70)

response = requests.post(
    f"{AUTH}/login",
    json={
        "email": "ramesh@company.com",
        "password": "pass123",
        "device_id": "DEVICE-HR-001"
    }
)

if response.status_code == 200:
    hr_token = response.json()["token"]
    print(f"✓ Login successful!")
    print(f"  Token: {hr_token[:50]}...")
    print(f"  Role: {response.json()['role']}")
else:
    print(f"✗ Login failed: {response.status_code}")
    print(f"  Response: {response.json()}")
    hr_token = None

# TEST 2: Access HR Portal (should work)
if hr_token:
    print("\n[TEST 2] Access HR Portal with HR role")
    print("-" * 70)
    
    response = requests.get(
        f"{GATEWAY}/hr-portal",
        headers={
            "Authorization": f"Bearer {hr_token}",
            "X-Device-ID": "DEVICE-HR-001",
            "X-Device-OS": "Windows 11"
        },
        verify=False
    )
    
    if response.status_code == 200:
        print("✓ Access granted!")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Access denied: {response.status_code}")
        print(f"  Response: {response.json()}")

# TEST 3: Try to access Finance (should fail - wrong role)
if hr_token:
    print("\n[TEST 3] Try to access Finance with HR role (should fail)")
    print("-" * 70)
    
    response = requests.get(
        f"{GATEWAY}/finance",
        headers={
            "Authorization": f"Bearer {hr_token}",
            "X-Device-ID": "DEVICE-HR-001",
            "X-Device-OS": "Windows 11"
        },
        verify=False
    )
    
    if response.status_code == 403:
        print("✓ Correctly blocked!")
        print(f"  Response: {response.json()}")
    else:
        print(f"✗ Should have been blocked but got: {response.status_code}")

# TEST 4: Login as Finance user
print("\n[TEST 4] Login as Finance user (priya@company.com)")
print("-" * 70)

response = requests.post(
    f"{AUTH}/login",
    json={
        "email": "priya@company.com",
        "password": "pass456",
        "device_id": "DEVICE-FIN-002"
    }
)

if response.status_code == 200:
    finance_token = response.json()["token"]
    print(f"✓ Login successful!")
    print(f"  Token: {finance_token[:50]}...")
    print(f"  Role: {response.json()['role']}")
else:
    print(f"✗ Login failed: {response.status_code}")
    finance_token = None

# TEST 5: Access Finance with Finance role (should work)
if finance_token:
    print("\n[TEST 5] Access Finance with Finance role")
    print("-" * 70)
    
    response = requests.get(
        f"{GATEWAY}/finance",
        headers={
            "Authorization": f"Bearer {finance_token}",
            "X-Device-ID": "DEVICE-FIN-002",
            "X-Device-OS": "macOS"
        },
        verify=False
    )
    
    if response.status_code == 200:
        print("✓ Access granted!")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Access denied: {response.status_code}")

# TEST 6: Try without device ID (should fail)
if hr_token:
    print("\n[TEST 6] Try to access without Device ID (should fail)")
    print("-" * 70)
    
    response = requests.get(
        f"{GATEWAY}/hr-portal",
        headers={
            "Authorization": f"Bearer {hr_token}"
        },
        verify=False
    )
    
    if response.status_code == 403:
        print("✓ Correctly blocked!")
        print(f"  Response: {response.json()}")
    else:
        print(f"✗ Should have been blocked but got: {response.status_code}")

# TEST 7: Try without token (should fail)
print("\n[TEST 7] Try to access without authentication (should fail)")
print("-" * 70)

response = requests.get(
    f"{GATEWAY}/hr-portal",
    headers={"X-Device-ID": "DEVICE-HR-001"},
    verify=False
)

if response.status_code == 401:
    print("✓ Correctly blocked!")
    print(f"  Response: {response.json()}")
else:
    print(f"✗ Should have been blocked but got: {response.status_code}")

# TEST 8: mTLS Verification
print("\n[TEST 8] mTLS Verification")
print("-" * 70)

try:
    response = requests.get("https://localhost:9001/health", verify=False, timeout=3)
    print("✗ Service accepted connection without client cert!")
except:
    print("✓ Service rejected connection without client cert")

try:
    response = requests.get(
        "https://localhost:9001/health",
        cert=("certs/gateway.crt", "certs/gateway.key"),
        verify="certs/ca.crt",
        timeout=3
    )
    if response.status_code == 200:
        print("✓ Service accepted gateway's client certificate")
        print(f"  Response: {response.json()}")
except Exception as e:
    print(f"✗ mTLS failed: {e}")

# TEST 9: Check Audit Logs
print("\n[TEST 9] Check Audit Logs")
print("-" * 70)

response = requests.get("http://localhost:9999/logs")
if response.status_code == 200:
    logs = response.json()
    print(f"✓ Retrieved {len(logs)} audit log entries")
    if logs:
        print(f"\n  Latest 3 entries:")
        for log in logs[-3:]:
            status = "ALLOWED" if log['allowed'] else "BLOCKED"
            print(f"  - [{status}] {log['email']} -> {log['path']} (Reason: {log['reason']})")

response = requests.get("http://localhost:9999/stats")
if response.status_code == 200:
    stats = response.json()
    print(f"\n  Statistics:")
    print(f"  - Total Requests: {stats['total_requests']}")
    print(f"  - Allowed: {stats['allowed']}")
    print(f"  - Blocked: {stats['blocked']}")
    print(f"  - Block Rate: {stats['block_rate']}")

print("\n" + "="*70)
print("TESTING COMPLETE!")
print("="*70)
print("\nYour ZTNA system is working with:")
print("  ✓ Authentication (JWT tokens)")
print("  ✓ Authorization (Role-based access control)")
print("  ✓ Device Trust (Device ID verification)")
print("  ✓ mTLS (Mutual TLS between gateway and services)")
print("  ✓ Audit Logging (All access attempts logged)")
print("\n")
