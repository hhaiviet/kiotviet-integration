# Scripts Directory

This directory contains all operational scripts organized by functionality.

## Structure

```
scripts/
├── README.md                           # This file
├── token/                             # Token management scripts
│   ├── check_token.py
│   ├── create_sample_token.py
│   ├── create_token_file.py
│   ├── fix_deps_token.py
│   ├── get_real_token.py
│   ├── install_and_run_token.py
│   ├── quick_token.py
│   ├── run_token_final.py
│   ├── run_token_on_pi.py
│   ├── show_token_result.py
│   └── token_status.py
├── dags/                              # Airflow DAGs for orchestration
├── kiotviet_auto_token_enhanced.py    # Enhanced token automation
├── kiotviet_auto_token_seleniumwire.py # Main token automation (tracked)
├── kiotviet_invoice_details.py        # Invoice sync CLI (tracked)
├── kiotviet_product_exporter.py       # Product export CLI (tracked)
├── kiotviet_run_all.py                # Main CLI wrapper (tracked)
├── auto_sync_on_pi.py                 # Pi synchronization
├── dashboard_etl.py                   # Dashboard ETL
├── dashboard_etl_fixed.py             # Fixed dashboard ETL
├── install_and_test_pi.py             # Pi installation and testing
├── n8n_kiotviet_workflow.json         # N8N workflow configuration
├── n8n_kiotviet_workflow_v2.json      # N8N workflow v2
├── pi_auto_sync.py                    # Pi auto sync
├── pre_deploy_check.py                # Pre-deployment checks
├── quick_sync.py                      # Quick sync utility
├── remote_debug.py                    # Remote debugging
├── run_all_scripts.py                 # Script runner
├── run_auto_sync.py                   # Auto sync runner
├── run_bash_sync.py                   # Bash sync runner
├── run_etl.py                         # ETL runner
├── run_pi_sync_now.py                 # Immediate Pi sync
├── run_sync_scripts.py                # Sync script runner
├── setup_cron.py                      # Cron setup
├── setup_n8n_workflow.py             # N8N workflow setup
├── setup_systemd.py                  # Systemd setup
└── upload_and_run_pi_sync.py         # Upload and run Pi sync
```

## Main Entry Points

### Core Scripts (Tracked in Git)
- **kiotviet_run_all.py**: Main CLI wrapper for running both invoice sync and product export
- **kiotviet_invoice_details.py**: CLI for invoice synchronization only
- **kiotviet_product_exporter.py**: CLI for product export only
- **kiotviet_auto_token_seleniumwire.py**: Automated token management with Selenium

### Token Management
Use scripts in the `token/` directory for token-related operations:
- `get_real_token.py`: Get valid access token
- `check_token.py`: Verify token status
- `quick_token.py`: Quick token generation

### Synchronization
- `quick_sync.py`: Quick data sync
- `run_pi_sync_now.py`: Immediate Pi synchronization
- `auto_sync_on_pi.py`: Automated Pi sync

### ETL Operations
- `run_etl.py`: Run ETL pipeline
- `dashboard_etl_fixed.py`: Fixed dashboard ETL