#!/usr/bin/env python3
"""
Test KiotViet login API with different payloads
Thử login với các payload khác nhau để tìm cách đúng
"""

import requests
import json

def test_login(payload_name, payload, headers=None):
    """Test login with specific payload."""
    print(f"\n{'='*70}")
    print(f"Testing: {payload_name}")
    print('='*70)
    
    url = "https://api-man1.kiotviet.vn/api/account/login"
    params = {"quan-ly": "true"}
    
    if headers is None:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Retailer": "248minimart",
        }
    
    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Headers: {json.dumps({k: v[:50] if len(str(v)) > 50 else v for k, v in headers.items()}, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, params=params, timeout=30)
        print(f"\nStatus: {response.status_code}")
        
        data = response.json()
        print(f"Response (truncated):")
        print(json.dumps(data, indent=2)[:500])
        
        if response.status_code == 200 and data.get("isSuccess"):
            print(f"\n✅ SUCCESS! Got token: {data.get('token', '')[:40]}...")
            return True
        else:
            print(f"\n❌ FAILED: {data}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

# Test different payloads
payloads = [
    ("Simple login", {
        "username": "0913431718",
        "password": "68686868",
        "RememberMe": False,
        "ShowCaptcha": False,
        "Language": "vi-VN",
        "LatestBranchId": 291407
    }),
    
    ("With model wrapper", {
        "model": {
            "UserName": "0913431718",
            "Password": "68686868",
            "RememberMe": False,
            "ShowCaptcha": False,
            "Language": "vi-VN",
            "LatestBranchId": 291407
        }
    }),
    
    ("With IsManageSide", {
        "model": {
            "RememberMe": True,
            "ShowCaptcha": False,
            "UserName": "0913431718",
            "Password": "68686868",
            "Language": "vi-VN",
            "LatestBranchId": 291407
        },
        "IsManageSide": True,
        "FingerPrintKey": "test"
    }),
]

print("\nTesting KiotViet Login API\n")

for name, payload in payloads:
    test_login(name, payload)

print("\n" + "="*70)
print("Test complete!")
print("="*70)
