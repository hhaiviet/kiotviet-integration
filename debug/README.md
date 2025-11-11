# Debug Directory

This directory contains test scripts, debugging utilities, and development tools.

## Structure

```
debug/
├── README.md                    # This file
├── test_api_client.py          # API client testing
├── test_api_complete.py        # Complete API testing
├── test_endpoints.py           # Endpoint testing
├── test_monitor_locally.py     # Local monitoring tests
├── test_scripts_on_pi.py       # Pi script testing
├── test_simple.py              # Simple functionality tests
├── test_token_api.py           # Token API testing
├── QUICK_START.py              # Quick start development script
├── upload_token_to_pi.py       # Token upload testing
└── test.txt                    # Test data file
```

## Usage

### API Testing
- **test_api_client.py**: Test KiotViet API client functionality
- **test_api_complete.py**: Comprehensive API testing
- **test_endpoints.py**: Test specific API endpoints
- **test_token_api.py**: Test token API operations

### System Testing
- **test_monitor_locally.py**: Test monitoring functions locally
- **test_scripts_on_pi.py**: Test scripts on Raspberry Pi
- **test_simple.py**: Simple functionality tests

### Development
- **QUICK_START.py**: Quick development setup and testing
- **upload_token_to_pi.py**: Test token upload to Pi
- **test.txt**: Test data for debugging

## Running Tests

Most test scripts can be run directly:
```bash
python debug/test_api_client.py
python debug/test_simple.py
```

Make sure to have valid credentials and configuration before running API tests.