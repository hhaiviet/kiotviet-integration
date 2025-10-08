# KiotViet Integration

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Automated integration tool for KiotViet API - Invoice synchronization, Product export, Token management, and Cloud storage uploads.

## 🚀 Features

- ✅ **Automated Token Management**: Selenium-based authentication with retry logic
- ✅ **Incremental Invoice Sync**: Efficient synchronization with checkpointing
- ✅ **Product Data Export**: Comprehensive product catalog export
- ✅ **Cloud Storage**: Azure Blob Storage integration
- ✅ **Robust Error Handling**: Comprehensive retry and error recovery
- ✅ **Progress Tracking**: Real-time progress bars and detailed logging
- ✅ **Docker Support**: Containerized deployment
- ✅ **CI/CD Ready**: GitHub Actions workflows
- ✅ **CLI Interface**: Command-line tools for all operations

## 📦 Installation

### Prerequisites

- Python 3.8+
- Chrome browser (for token automation)
- Azure Storage account (optional, for cloud uploads)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/hhaiviet/kiotviet-integration.git
cd kiotviet-integration

# Install dependencies
make install

# For development
make dev-install
```

### Docker Setup

```bash
# Build and run with Docker
docker-compose up --build

# Or use the provided Dockerfile
docker build -t kiotviet-integration .
docker run -v $(pwd)/data:/app/data kiotviet-integration
```

## ⚙️ Configuration

### Environment Variables

1. **Copy environment template**:
```bash
cp .env.example .env
```

2. **Configure KiotViet credentials** in `.env`:
```bash
# Required: KiotViet login credentials
KIOTVIET_USERNAME=your_username
KIOTVIET_PASSWORD=your_password

# Optional: Pre-configured retailer/branch IDs
KIOTVIET_RETAILER_ID=your_retailer_id
KIOTVIET_BRANCH_ID=your_branch_id
```

3. **Generate API token** (automated):
```bash
python scripts/kiotviet_auto_token_seleniumwire.py
```
This creates `data/credentials/token.json` with `access_token`, `retailer_id`, and `branch_id`.

### Azure Blob Storage (Optional)

Add to `.env` for cloud storage:
```bash
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER=kiotviet-data
```

## 🎯 Usage

### Command Line Interface

#### Run Complete Integration
```bash
# Execute both invoice sync and product export
python scripts/kiotviet_run_all.py

# Options
python scripts/kiotviet_run_all.py --full-invoice     # Full invoice sync (ignore checkpoint)
python scripts/kiotviet_run_all.py --product-page-size 50  # Custom page size
python scripts/kiotviet_run_all.py --skip-invoice     # Skip invoice sync
```

#### Individual Operations
```bash
# Invoice synchronization only
python scripts/kiotviet_invoice_details.py --full

# Product export only
python scripts/kiotviet_product_exporter.py --page-size 200 --output custom_products.csv
```

#### Token Management
```bash
# Automated token retrieval
python scripts/kiotviet_auto_token_seleniumwire.py
```

### Python API

```python
from src.services import InvoiceService, ProductService

# Initialize services
invoice_service = InvoiceService()
product_service = ProductService()

# Synchronize invoices (incremental by default)
result = invoice_service.sync()
print(f"Synced {result.invoices} invoices, {result.lines} lines")

# Export products
result = product_service.export(page_size=100)
print(f"Exported {result.products} products")
```

### Scheduled Execution

#### Cron Job Setup
```bash
# Edit crontab
crontab -e

# Add line for every 30 minutes (8 AM - 11 PM)
*/30 8-23 * * * /path/to/kiotviet-integration/scripts/run_all_cron.sh

# Or use the provided script
bash scripts/setup_cron.sh
```

#### Manual Cron Execution
```bash
# Test cron script
./scripts/run_all_cron.sh
```

## 🏗️ Architecture

```
src/
├── api/           # HTTP client and API wrappers
│   ├── client.py         # KiotVietClient with retry logic
│   └── exceptions.py     # Custom exceptions
├── services/      # Business logic layer
│   ├── base_service.py   # Common service functionality
│   ├── invoice_service.py # Invoice synchronization
│   ├── product_service.py # Product export
│   └── token_service.py  # Token management
├── models/        # Data models and schemas
├── exporters/     # Export utilities
├── utils/         # Shared utilities
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging setup
│   └── azure_blob.py    # Cloud storage
└── cli/           # Command-line interface
```

### Key Components

#### KiotVietClient
- HTTP client with automatic retry logic
- Exponential backoff for rate limits
- Comprehensive error handling
- Session management for connection pooling

#### BaseService
- Common initialization for all services
- Configuration loading
- Token and client management
- Path resolution utilities

#### InvoiceService
- Incremental synchronization with checkpoints
- Batch processing with progress tracking
- Detail fetching with error recovery
- CSV export with proper encoding

#### ProductService
- Full catalog export
- Configurable field selection
- Pagination handling
- Optimized batch processing

## 🔧 API Reference

### InvoiceService

```python
class InvoiceService(BaseService):
    def sync(self, incremental: bool = True) -> InvoiceSyncResult:
        """Synchronize invoices from KiotViet API.

        Args:
            incremental: Use checkpoint for incremental sync

        Returns:
            InvoiceSyncResult with sync statistics
        """
```

### ProductService

```python
class ProductService(BaseService):
    def export(
        self,
        *,
        page_size: Optional[int] = None,
        fields: Sequence[str] = DEFAULT_PRODUCT_FIELDS,
        output_file: Optional[Path] = None,
    ) -> ProductExportResult:
        """Export products to CSV.

        Args:
            page_size: Products per API page
            fields: Fields to include in export
            output_file: Custom output path

        Returns:
            ProductExportResult with export statistics
        """
```

### KiotVietClient

```python
class KiotVietClient:
    def get(self, endpoint: str, *, headers: Dict[str, str], **kwargs) -> Dict:
        """GET request with retry logic"""

    def post(self, endpoint: str, *, headers: Dict[str, str], json_payload: Dict, **kwargs) -> Dict:
        """POST request with retry logic"""
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/unit/test_api_client.py -v
pytest tests/integration/ -v

# Lint code
make lint
```

## 📊 Monitoring

### Logs
- Application logs: `data/logs/kiotviet.log`
- Cron execution logs: `cron.log`
- Progress tracking in real-time

### Metrics
- Invoice sync: invoices processed, lines exported, duration
- Product export: products exported, duration
- API calls: success rate, retry counts, error types

## 🚀 Performance Optimization

- **Incremental Sync**: Checkpoint-based synchronization
- **Batch Processing**: Configurable page sizes
- **Connection Pooling**: HTTP session reuse
- **Exponential Backoff**: Smart retry delays
- **Progress Tracking**: Efficient tqdm progress bars
- **Memory Management**: Streaming CSV writes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
make dev-install

# Run tests and linting
make test
make lint

# Format code
make format
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Troubleshooting

### Common Issues

**Chrome Driver Issues**
```bash
# Update webdriver-manager
pip install --upgrade webdriver-manager
```

**Token Authentication Fails**
- Verify KiotViet credentials
- Check network connectivity
- Ensure Chrome browser is available

**API Rate Limits**
- Increase retry delays in config
- Reduce page sizes
- Implement backoff strategies

**Azure Upload Fails**
- Verify connection string
- Check container permissions
- Validate blob names

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python scripts/kiotviet_run_all.py
```
