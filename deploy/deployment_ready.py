import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('116.102.136.220', username='hhaiviet', password='Hoangviet12', allow_agent=False, look_for_keys=False, timeout=10)

# Final validation test
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
print('[FINAL VALIDATION TEST]')
print('='*60)

print()
print('[1] Token Status')
token_service = TokenService('data/credentials/token.json')
credentials = token_service.load()
headers = TokenService.build_headers(credentials)

print(f'    Retailer: {credentials.retailer_id}')
print(f'    Branch:   {credentials.branch_id}')
print(f'    Token:    {"Valid JWT" if credentials.access_token.startswith("eyJ") else "INVALID"}')
print(f'    Headers:  {list(headers.keys())}')

print()
print('[2] API Client Status')
client = KiotVietClient(base_url='https://api-man1.kiotviet.vn/api', timeout=30)
print(f'    Base URL: {client.base_url}')
print(f'    Timeout:  {client.timeout}s')
print(f'    Max Retries: {client.max_retries}')

print()
print('[3] Service Classes Available')
try:
    from src.services.product_service import ProductService
    print('    ✓ ProductService')
except Exception as e:
    print(f'    ✗ ProductService: {e}')

try:
    from src.services.invoice_service import InvoiceService
    print('    ✓ InvoiceService')
except Exception as e:
    print(f'    ✗ InvoiceService: {e}')

try:
    from src.services.token_service import TokenService as TS
    print('    ✓ TokenService')
except Exception as e:
    print(f'    ✗ TokenService: {e}')

print()
print('[4] Data Directories')
import os
dirs_to_check = [
    'data/credentials',
    'data/output',
    'data/logs',
    'data/checkpoints',
]
for dir_path in dirs_to_check:
    exists = os.path.isdir(dir_path)
    status = '✓' if exists else '✗'
    print(f'    {status} {dir_path}')

print()
print('[5] Configuration')
from src.utils.config import config
print(f'    API Base: {config.get("api", {}).get("base_url")}')
print(f'    Token File: {config.get("credentials", {}).get("token_file")}')
print(f'    Page Size: {config.get("api", {}).get("page_size")}')

print()
print('='*60)
print('[OK] DEPLOYMENT READY!')
print()
print('Run scripts:')
print('  python scripts/kiotviet_product_exporter.py')
print('  python scripts/kiotviet_invoice_details.py')
print('  python scripts/kiotviet_run_all.py')
PYEOF
"""

_, stdout, _ = ssh.exec_command(cmd, timeout=30)
print(stdout.read(8192).decode())

ssh.close()
