"""
Production Setup Script
اسکریپت راه‌اندازی production
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_command(command: str, description: str):
    """اجرای یک دستور"""
    try:
        logger.info(f"Running: {description}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"✅ {description} completed successfully")
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed: {e.stderr}")
        return False


def setup_production():
    """راه‌اندازی production"""
    print("=" * 60)
    print("Production Setup")
    print("=" * 60)
    
    steps = [
        ("python scripts/create_migration.py", "Creating database tables"),
        ("python scripts/seed_initial_data.py", "Seeding initial data"),
    ]
    
    success = True
    for command, description in steps:
        if not run_command(command, description):
            success = False
            logger.error(f"Failed at step: {description}")
            break
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Production setup completed successfully!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("   1. Review and update configuration files")
        print("   2. Set up SSL/TLS certificates")
        print("   3. Configure backup procedures")
        print("   4. Set up monitoring and alerting")
        print("   5. Train team using docs/TRAINING_MATERIAL.md")
    else:
        print("\n" + "=" * 60)
        print("❌ Production setup failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    setup_production()

