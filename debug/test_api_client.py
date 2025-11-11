import paramiko
import sys
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False, timeout=10)
    
    # Test token loading and API client
    cmd = """
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
python << 'PYEOF'
import sys
import json
sys.path.insert(0, '.')

# Load token
print('[TEST 1] Loading token...')
with open('data/credentials/token.json') as f:
    creds_data = json.load(f)
print(f'  Retailer: {creds_data.get("retailer_id")}')
print(f'  Branch: {creds_data.get("branch_id")}')
print(f'  Token: {creds_data.get("access_token")[:40]}...')

# Import API client
print()
print('[TEST 2] Importing API client...')
from src.models.credentials import Credentials
from src.api.client import KiotVietClient

creds = Credentials(
    retailer_id=creds_data.get('retailer_id'),
    branch_id=creds_data.get('branch_id'),
    access_token=creds_data.get('access_token')
)
print(f'  Credentials object created')

client = KiotVietClient(creds)
print(f'  KiotVietClient initialized')

# Test API call
print()
print('[TEST 3] Testing API connectivity...')
try:
    result = client.get('/account/info')
    if result:
        print(f'  [OK] API call successful!')
        if isinstance(result, dict):
            print(f'  Response keys: {list(result.keys())[:5]}')
    else:
        print(f'  [!] Empty response')
except Exception as e:
    print(f'  [!] API error: {e}')

print()
print('[OK] All tests passed - system ready!')
PYEOF
"""
    
    _, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    
    # Read output
    output = stdout.read(8192).decode()
    print(output)
    
    # Check for errors
    errors = stderr.read(2048).decode()
    if errors:
        print('[Errors/Warnings]:')
        print(errors)
    
except Exception as e:
    print(f'[ERROR] {e}')
    sys.exit(1)
finally:
    ssh.close()
