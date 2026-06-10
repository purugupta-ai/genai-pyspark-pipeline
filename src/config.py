import os
import logging
from pathlib import Path

# Set up base project directory path
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directory paths
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

# File names
CUSTOMERS_FILE = RAW_DATA_DIR / "customers.csv"
PRODUCTS_FILE = RAW_DATA_DIR / "products.csv"
ORDERS_FILE = RAW_DATA_DIR / "orders.csv"

def setup_logging(logger_name: str) -> logging.Logger:
    """
    Configures and returns a logger instance for the application.

    Args:
        logger_name (str): The name of the logger (usually __name__).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(logger_name)