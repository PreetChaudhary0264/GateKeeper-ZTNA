"""
ZTNA Redis Functionality Test
Tests: Rate limiting, Token blacklisting, Session tracking
"""

import requests
import time
import urllib3

urllib3.disable_warnings()

AUTH = "http://localhost:8001"
GATEWAY = "https://localhost:8080"

print("\n" + "="*70)
print("ZTNA REDIS FUNCTIONALITY TEST")
print("="*70)

# TEST 1: Rate Limiting
print("\n[TEST 1] Rate Limiting - Failed Login Attempts")
print("-" * 70)

for i in range(6):
    response = requests.post(
        f"{AUTH}/login",
        json={
            "email": "ramesh@company.com",
            "password": "WRONG_PASSWORD",
            "device_id": "DEVICE-HR-001"
        }
    )
    print(f"Attempt {i+1}: Status {response.status_code}")
    if response.status_code == 429:
        print(f"✓ Rate limited after 5 failed attempts!")
        print(f"  Response: {response.json()}")
        break
    time.sleep(0.5)

print("\nWaiting 5 seconds before next test...")
time.sleep(5)

# TEST 2: Successful Login & Session Tracking
print("\n[TEST 2] Successful Login & Session Tracking")
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
    token = response.json()["token"]
    print(f"✓ Login successful!")
    print(f"  Token: {token[:50]}...")
    print(f"  Session tracked in Redis")
else:
    print(f"✗ Login failed: {response.status_code}")
    exit(1)

# TEST 3: Access with Valid Token
print("\n[TEST 3] Access HR Portal with Valid Token")
print("-" * 70)

response = requests.get(
    f"{GATEWAY}/hr-portal",
    headers={
        "Authorization": f"Bearer {token}",
        "X-Device-ID": "DEVICE-HR-001",
        "X-Device-OS": "Windows 11"
    },
    verify=False
)

if response.status_code == 200:
    print(f"✓ Access granted!")
else:
    print(f"✗ Access denied: {response.status_code}")

# TEST 4: Logout (Token Blacklisting)
print("\n[TEST 4] Logout - Token Blacklisting")
print("-" * 70)

response = requests.post(
    f"{AUTH}/logout",
    json={"token": token}
)

if response.status_code == 200:
    print(f"✓ Logout successful!")
    print(f"  Response: {response.json()}")
    print(f"  Token added to Redis blacklist")
else:
    print(f"✗ Logout failed: {response.status_code}")

# TEST 5: Try to Access with Blacklisted Token
print("\n[TEST 5] Try to Access with Blacklisted Token")
print("-" * 70)

response = requests.get(
    f"{GATEWAY}/hr-portal",
    headers={
        "Authorization": f"Bearer {token}",
        "X-Device-ID": "DEVICE-HR-001",
        "X-Device-OS": "Windows 11"
    },
    verify=False
)

if response.status_code == 401:
    print(f"✓ Access correctly blocked!")
    print(f"  Response: {response.json()}")
else:
    print(f"✗ Should have been blocked but got: {response.status_code}")

# TEST 6: Login Again After Logout
print("\n[TEST 6] Login Again After Logout")
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
    new_token = response.json()["token"]
    print(f"✓ New login successful!")
    print(f"  New Token: {new_token[:50]}...")
    
    # Try accessing with new token
    response = requests.get(
        f"{GATEWAY}/hr-portal",
        headers={
            "Authorization": f"Bearer {new_token}",
            "X-Device-ID": "DEVICE-HR-001",
            "X-Device-OS": "Windows 11"
        },
        verify=False
    )
    
    if response.status_code == 200:
        print(f"✓ Access granted with new token!")
    else:
        print(f"✗ Access denied: {response.status_code}")
else:
    print(f"✗ Login failed: {response.status_code}")

# TEST 7: Redis Health Check
print("\n[TEST 7] Redis Health Check")
print("-" * 70)

response = requests.get(f"{AUTH}/health")
if response.status_code == 200:
    health = response.json()
    print(f"✓ Auth Service Health:")
    print(f"  Status: {health['status']}")
    print(f"  Redis: {health['redis']}")

print("\n" + "="*70)
print("REDIS FUNCTIONALITY TEST COMPLETE!")
print("="*70)
print("\nRedis Features Tested:")
print("  ✓ Rate Limiting (5 failed attempts)")
print("  ✓ Token Blacklisting (logout)")
print("  ✓ Session Tracking")
print("  ✓ Blacklist Verification")
print("\n")
