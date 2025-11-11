#!/usr/bin/env python3
"""
Final validation that everything is ready on Pi
"""

import paramiko
import json

PI_IP = "116.102.136.220"
PI_USER = "hhaiviet"
PI_PASSWORD = "Hoangviet12"
PI_PROJECT_DIR = "/home/hhaiviet/kiotviet-integration"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("[*] Connecting to Pi...")
ssh.connect(PI_IP, username=PI_USER, password=PI_PASSWORD, allow_agent=False, look_for_keys=False)

print("[OK] Connected\n")
print("="*70)

# Test 1: Project structure
print("[TEST 1] Project structure")
_, stdout, _ = ssh.exec_command(f"ls -la {PI_PROJECT_DIR}/scripts/kiotviet_*.py | wc -l")
count = stdout.read().decode().strip()
print(f"  ✓ Found {count} kiotviet scripts")

_, stdout, _ = ssh.exec_command(f"test -f {PI_PROJECT_DIR}/data/credentials/token.json && echo OK || echo MISSING")
result = stdout.read().decode().strip()
if result == "OK":
    print("  ✓ Token file exists")
else:
    print("  ✗ Token file missing!")

# Test 2: Token loading
print("\n[TEST 2] Token loading")
_, stdout, stderr = ssh.exec_command(f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate
python3 << 'EOF'
import json
with open('data/credentials/token.json') as f:
    token = json.load(f)
    print(f"Retailer: {{token.get('retailer_id')}}")
    print(f"Branch: {{token.get('branch_id')}}")
    print(f"Token length: {{len(token.get('access_token', ''))}}")
EOF
""")
print(stdout.read().decode())

# Test 3: Module imports
print("[TEST 3] Required modules")
_, stdout, stderr = ssh.exec_command(f"""
cd {PI_PROJECT_DIR}
source venv/bin/activate
python3 << 'EOF'
try:
    import yaml
    print("  ✓ yaml")
except: print("  ✗ yaml")

try:
    import requests
    print("  ✓ requests")
except: print("  ✗ requests")

try:
    import pandas
    print("  ✓ pandas")
except: print("  ✗ pandas")

try:
    import pydantic
    print("  ✓ pydantic")
except: print("  ✗ pydantic")

try:
    from src.models.credentials import Credentials
    print("  ✓ src.models.credentials")
except Exception as e: 
    print(f"  ✗ src.models: {{e}}")

try:
    from src.api.client import KiotVietClient
    print("  ✓ src.api.client")
except Exception as e:
    print(f"  ✗ src.api: {{e}}")

try:
    from src.services.token_service import TokenService
    print("  ✓ src.services.token_service")
except Exception as e:
    print(f"  ✗ src.services: {{e}}")
EOF
""")
print(stdout.read().decode())

err = stderr.read().decode()
if err:
    print("Errors:")
    print(err[:500])

print("="*70)
print("\n[OK] Validation complete!")
print("\nNext: Run the sync script")
print(f"  ssh {PI_USER}@{PI_IP}")
print(f"  cd {PI_PROJECT_DIR}")
print(f"  source venv/bin/activate")
print(f"  python scripts/kiotviet_run_all.py")

ssh.close()
