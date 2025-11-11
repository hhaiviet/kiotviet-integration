import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False, timeout=10)
    
    # Test token loading and API client with correct imports
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

# Import correct classes
print()
print('[TEST 2] Initializing services...')
from src.services.token_service import TokenService
from src.api.client import KiotVietClient

# Load via TokenService
token_service = TokenService('data/credentials/token.json')
credentials = token_service.load()
headers = TokenService.build_headers(credentials)

print(f'  TokenService loaded credentials')
print(f'  Headers prepared: {list(headers.keys())}')

# Initialize client
client = KiotVietClient(
    base_url='https://api-man1.kiotviet.vn/api',
    timeout=30
)
print(f'  KiotVietClient initialized')

# Test API call
print()
print('[TEST 3] Testing API connectivity...')
try:
    result = client.get('/account/info', headers=headers)
    if result:
        print(f'  [OK] API call successful!')
        print(f'  Response type: {type(result).__name__}')
        if isinstance(result, dict):
            keys = list(result.keys())[:5]
            print(f'  Response keys: {keys}')
    else:
        print(f'  [!] Empty response')
except Exception as e:
    print(f'  [!] API error: {type(e).__name__}: {str(e)[:100]}')

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
    if errors and 'Traceback' in errors:
        print('[ERRORS]:')
        print(errors)
    
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    ssh.close()
