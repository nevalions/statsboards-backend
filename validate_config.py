#!/usr/bin/env python3
"""
Configuration validation script.
Run this script to validate all configuration settings before starting the application.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import settings
from src.logging_config import setup_logging

setup_logging()


def main():
    try:
        print("Starting configuration validation...")
        settings.validate_all()
        print("✓ Configuration validation successful")
        return 0
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
