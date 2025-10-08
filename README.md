# KiotViet Integration

Automated integration tool for KiotViet API - Invoice sync, Product export, and Token management.

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/hhaiviet/kiotviet-integration.git
cd kiotviet-integration

# Install dependencies
make install

# For development
make dev-install
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your KiotViet credentials
3. Generate `data/credentials/token.json` using the Selenium helper script:
   - `python scripts/kiotviet_auto_token_seleniumwire.py`
   - The file must contain `access_token`, `retailer_id`, and `branch_id`.


### Usage

#### CLI Commands

```bash
# Run both invoice sync and product export sequentially
python scripts/kiotviet_run_all.py
```

Options:
- `--full-invoice`: ignore checkpoint for invoices
- `--product-page-size N`: override product page size
- `--product-output PATH`: custom CSV path
- `--skip-invoice` / `--skip-product`: run only one part

```bash
# Get access token
kiotviet auth login

# Sync invoices
kiotviet sync invoices --incremental

# Export products
kiotviet export products --format csv

# Run with Docker
docker-compose up
```

#### As Python Module

```python
from src.services import InvoiceService, ProductService

# Initialize services
invoice_service = InvoiceService()
product_service = ProductService()

# Sync invoices
invoice_service.sync_all()

# Export products
products = product_service.get_all()
product_service.export_to_csv(products)
```

## 📦 Features

- ✅ Automated token management with Selenium
- ✅ Incremental invoice synchronization
- ✅ Product data export (CSV/Excel)
- ✅ Retry logic and error handling
- ✅ Progress tracking and logging
- ✅ Docker support
- ✅ CI/CD with GitHub Actions

## 🏗️ Architecture

```
src/
├── api/        # API clients and authentication
├── services/   # Business logic
├── models/     # Data models
├── exporters/  # Export handlers
├── utils/      # Utilities
└── cli/        # Command-line interface
```

## � Automated Scheduling (GitHub Actions)

### Setup GitHub Actions

1. **Add Repository Secrets** (Settings → Secrets and variables → Actions):
   ```
   AZURE_STORAGE_CONNECTION_STRING = DefaultEndpointsProtocol=https;AccountName=...
   AZURE_STORAGE_CONTAINER = kiotviet-data
   KIOTVIET_USERNAME = your_username
   KIOTVIET_PASSWORD = your_password
   ```

2. **Enable Workflows**:
   - Production: `.github/workflows/sync.yml` (runs every 30 minutes, 8 AM - 11 PM UTC)
   - Testing: `.github/workflows/sync-test.yml` (runs every 2 minutes for testing)

3. **Monitor Runs**:
   - Go to Actions tab in your repository
   - Check workflow runs and logs
   - Failed runs will upload log artifacts

### Manual Trigger

You can also trigger the sync manually:
- Go to Actions → KiotViet Data Sync → Run workflow

### Alternative Schedulers

For local development, you can use:
- **Python APScheduler**: `python python_scheduler.py`
- **Bash loop**: `./cron_simulator.sh`

## �🧪 Testing

```bash
# Run all tests
make test

# Run specific test
pytest tests/unit/test_api_client.py -v

# Check coverage
pytest --cov=src --cov-report=html
```

## 📄 License

MIT License
