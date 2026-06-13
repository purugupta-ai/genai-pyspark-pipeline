"""
Daily Pipeline Scheduler
=======================
Automates the execution of the data generation and PySpark analytics pipeline.
"""

import schedule
import time
import subprocess
import sys
import logging
from datetime import datetime
from src.config import setup_logging

# Setup logging for the scheduler
logger = setup_logging("Scheduler")

def run_full_pipeline():
    """Executes the complete data generation and analytics suite."""
    start_time = datetime.now()
    logger.info(f"--- Starting Scheduled Pipeline Run: {start_time} ---")
    
    try:
        # 1. Run Data Generation
        logger.info("Executing Step 1: Data Generation (main.py)...")
        subprocess.run([sys.executable, "main.py"], check=True)
        
        # 2. Run Analytics Pipeline
        logger.info("Executing Step 2: Spark Analytics (run_analytics.py)...")
        subprocess.run([sys.executable, "run_analytics.py"], check=True)
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"--- Pipeline Completed Successfully at {end_time} (Duration: {duration}) ---")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"!!! Pipeline failed during execution of {e.cmd}. Error code: {e.returncode} !!!")
    except Exception as e:
        logger.error(f"!!! Unexpected error in scheduler: {str(e)} !!!")

# Schedule the task to run daily at midnight
schedule.every().day.at("00:00").do(run_full_pipeline)

if __name__ == "__main__":
    logger.info("Pipeline Scheduler Initialized.")
    logger.info("The pipeline is scheduled to run every day at 00:00.")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
