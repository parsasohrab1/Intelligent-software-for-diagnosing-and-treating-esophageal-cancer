#!/usr/bin/env python3
"""
تنظیم داده‌های داشبورد برای اجرای زنده
Setup dashboard data for live execution with saved data
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_live_dashboard():
    """Setup dashboard with saved data for live execution"""
    logger.info("=" * 60)
    logger.info("Setting Up Live Dashboard Data")
    logger.info("=" * 60)
    
    # Step 1: Save current data
    logger.info("\n[Step 1/3] Saving current data...")
    try:
        from scripts.save_current_data import save_current_data
        snapshot_path = save_current_data("data_snapshot.json")
        logger.info(f"✓ Data saved to: {snapshot_path}")
    except Exception as e:
        logger.error(f"❌ Failed to save data: {e}")
        return False
    
    # Step 2: Clear unnecessary data
    logger.info("\n[Step 2/3] Clearing unnecessary data...")
    try:
        from scripts.clear_unnecessary_data import clear_unnecessary_data
        clear_unnecessary_data(keep_synthetic=True)
        logger.info("✓ Unnecessary data cleared")
    except Exception as e:
        logger.error(f"❌ Failed to clear data: {e}")
        return False
    
    # Step 3: Restore saved data (to ensure clean state)
    logger.info("\n[Step 3/3] Restoring saved data...")
    try:
        from scripts.restore_saved_data import restore_saved_data
        if restore_saved_data("data_snapshot.json", clear_existing=True):
            logger.info("✓ Data restored successfully")
        else:
            logger.error("❌ Failed to restore data")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to restore data: {e}")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Live Dashboard Setup Complete!")
    logger.info("=" * 60)
    logger.info("\nDashboard is now configured with saved data.")
    logger.info("Every time you start the dashboard, it will use this data.")
    logger.info("\nTo start the dashboard:")
    logger.info("  python -m uvicorn app.main:app --reload")
    logger.info("  or")
    logger.info("  npm start (in frontend directory)")
    logger.info("=" * 60)
    
    return True


if __name__ == '__main__':
    setup_live_dashboard()
