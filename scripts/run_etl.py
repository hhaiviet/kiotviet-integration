#!/usr/bin/env python3
"""
KiotViet ETL - Production orchestration script
CLI entry point to run complete ETL pipeline
"""

import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestration import KiotVietETLPipeline


def main():
    """Run ETL pipeline"""
    pipeline = KiotVietETLPipeline()
    result = pipeline.run()
    return 0 if result.success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
