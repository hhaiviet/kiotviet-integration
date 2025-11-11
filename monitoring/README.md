# Monitoring Directory

This directory contains monitoring, checking, and debugging scripts and logs.

## Structure

```
monitoring/
├── README.md                    # This file
├── check_pi.py                 # Pi system checks
├── check_progress.py           # Progress monitoring
├── check_status.py             # Status checking
├── detailed_check.py           # Detailed system checks
├── final_validation.py         # Final validation checks
├── monitor_etl.py              # ETL monitoring
├── monitor_token.py            # Token monitoring
├── status_check.py             # General status checks
├── verify_pi.py                # Pi verification
├── deployment_output.log       # Deployment logs
└── token_output.log            # Token operation logs
```

## Usage

### System Monitoring
- **check_pi.py**: Check Pi system health and connectivity
- **status_check.py**: General system status checks
- **detailed_check.py**: Comprehensive system analysis

### Process Monitoring
- **monitor_etl.py**: Monitor ETL pipeline execution
- **monitor_token.py**: Monitor token operations
- **check_progress.py**: Track operation progress

### Validation
- **final_validation.py**: Final system validation
- **verify_pi.py**: Pi system verification

### Logs
- **deployment_output.log**: Deployment operation logs
- **token_output.log**: Token generation and validation logs