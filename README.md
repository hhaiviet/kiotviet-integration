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

## 🧪 Testing

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
