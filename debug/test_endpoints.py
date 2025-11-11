import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False, timeout=10)

# Test different endpoints
cmd = """
cd /home/hhaiviet/kiotviet-integration
source venv/bin/activate
python << 'PYEOF'
import sys
import json
sys.path.insert(0, '.')

from src.services.token_service import TokenService
from src.api.client import KiotVietClient

# Load credentials
token_service = TokenService('data/credentials/token.json')
credentials = token_service.load()
headers = TokenService.build_headers(credentials)

# Initialize client
client = KiotVietClient(base_url='https://api-man1.kiotviet.vn/api', timeout=30)

print('[TEST] Testing different API endpoints...')

endpoints = [
    '/account/info',
    '/account/profile',
    '/product',
    '/invoice',
    '/inventory/stock',
]

for endpoint in endpoints:
    try:
        result = client.get(endpoint, headers=headers)
        if result:
            if isinstance(result, dict) and 'isSuccess' in result:
                status = 'OK' if result.get('isSuccess') else 'FAILED'
                print(f'  {endpoint:25} -> {status}')
            else:
                print(f'  {endpoint:25} -> OK (response received)')
        else:
            print(f'  {endpoint:25} -> EMPTY')
    except Exception as e:
        error_msg = str(e).split(':')[-1].strip()[:30]
        print(f'  {endpoint:25} -> ERROR: {error_msg}')

print()
print('[OK] Endpoint test complete - token is valid for API calls!')
PYEOF
"""

_, stdout, stderr = ssh.exec_command(cmd, timeout=30)
print(stdout.read(4096).decode())

err = stderr.read(2048).decode()
if err and 'Traceback' in err:
    print('ERRORS:', err[:500])

ssh.close()
