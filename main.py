"""
Main entry point for synthetic e-commerce data generation pipeline.

This script:
1. Initializes the SyntheticDataGenerator
2. Generates synthetic customers, products, and orders
3. Saves datasets as Parquet files
4. Prints performance metrics and file sizes
5. Includes comprehensive error handling
"""

import logging
import sys
import time
from pathlib import Path

from src.config import (
    setup_logging,
    NUM_CUSTOMERS,
    NUM_PRODUCTS,
    NUM_ORDERS,
    RAW_DATA_DIR,
    CUSTOMERS_PARQUET,
    PRODUCTS_PARQUET,
    ORDERS_PARQUET,
)
from src.data_generator import SyntheticDataGenerator

logger = setup_logging(__name__)


def get_file_size_mb(filepath: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        filepath (Path): Path to the file
        
    Returns:
        float: File size in MB, rounded to 2 decimal places
    """
    if filepath.exists():
        return filepath.stat().st_size / (1024 * 1024)
    return 0.0


def main() -> int:
    """
    Main execution function for the data generation pipeline.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("=" * 70)
        logger.info("STARTING SYNTHETIC E-COMMERCE DATA GENERATION PIPELINE")
        logger.info("=" * 70)
        
        # Record start time
        start_time = time.time()
        
        # Initialize generator with default parameters
        logger.info("Initializing SyntheticDataGenerator...")
        generator = SyntheticDataGenerator(
            num_customers=NUM_CUSTOMERS,
            num_products=NUM_PRODUCTS,
            num_orders=NUM_ORDERS,
            random_seed=42,
        )
        
        # Create raw data directory if it doesn't exist
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory ready: {RAW_DATA_DIR}")
        
        # Generate all datasets
        logger.info("Generating synthetic datasets...")
        generation_start = time.time()
        
        customers_df, products_df, orders_df = generator.generate_all()
        
        generation_time = time.time() - generation_start
        logger.info(f"Data generation completed in {generation_time:.2f} seconds")
        
        # Save as Parquet files
        logger.info("Saving datasets as Parquet files...")
        save_start = time.time()
        
        # Save customers
        logger.info(f"Saving customers to {CUSTOMERS_PARQUET}...")
        customers_df.to_parquet(CUSTOMERS_PARQUET, index=False, compression="snappy")
        customers_size = get_file_size_mb(CUSTOMERS_PARQUET)
        logger.info(f"Customers parquet saved: {customers_size:.2f} MB")
        
        # Save products
        logger.info(f"Saving products to {PRODUCTS_PARQUET}...")
        products_df.to_parquet(PRODUCTS_PARQUET, index=False, compression="snappy")
        products_size = get_file_size_mb(PRODUCTS_PARQUET)
        logger.info(f"Products parquet saved: {products_size:.2f} MB")
        
        # Save orders
        logger.info(f"Saving orders to {ORDERS_PARQUET}...")
        orders_df.to_parquet(ORDERS_PARQUET, index=False, compression="snappy")
        orders_size = get_file_size_mb(ORDERS_PARQUET)
        logger.info(f"Orders parquet saved: {orders_size:.2f} MB")
        
        save_time = time.time() - save_start
        logger.info(f"Data saving completed in {save_time:.2f} seconds")
        
        # Total execution time
        total_time = time.time() - start_time
        
        # Print summary report
        print("\n" + "=" * 70)
        print("SYNTHETIC DATA GENERATION SUMMARY")
        print("=" * 70)
        
        print("\n📊 DATASETS GENERATED:")
        print(f"  • Customers:  {len(customers_df):>15,} records")
        print(f"  • Products:   {len(products_df):>15,} records")
        print(f"  • Orders:     {len(orders_df):>15,} records")
        print(f"  • Total rows: {len(customers_df) + len(products_df) + len(orders_df):>15,}")
        
        print("\n💾 PARQUET FILES CREATED:")
        print(f"  • {CUSTOMERS_PARQUET.name:<20} {customers_size:>10.2f} MB")
        print(f"  • {PRODUCTS_PARQUET.name:<20} {products_size:>10.2f} MB")
        print(f"  • {ORDERS_PARQUET.name:<20} {orders_size:>10.2f} MB")
        print(f"  • {'Total':20} {(customers_size + products_size + orders_size):>10.2f} MB")
        
        print("\n⏱️  EXECUTION TIMES:")
        print(f"  • Data Generation: {generation_time:>13.2f} seconds")
        print(f"  • Data Saving:     {save_time:>13.2f} seconds")
        print(f"  • Total Duration:  {total_time:>13.2f} seconds")
        
        print("\n📁 OUTPUT LOCATION:")
        print(f"  • {RAW_DATA_DIR}")
        
        print("\n✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70 + "\n")
        
        logger.info("Pipeline execution completed successfully")
        return 0
        
    except ImportError as e:
        logger.error(f"Import error: {e}", exc_info=True)
        print(f"\n❌ ERROR: Failed to import required module: {e}", file=sys.stderr)
        return 1
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        print(f"\n❌ ERROR: Required file not found: {e}", file=sys.stderr)
        return 1
        
    except PermissionError as e:
        logger.error(f"Permission denied: {e}", exc_info=True)
        print(
            f"\n❌ ERROR: Permission denied while accessing files: {e}",
            file=sys.stderr,
        )
        return 1
        
    except MemoryError:
        logger.error("Insufficient memory to generate datasets", exc_info=True)
        print(
            "\n❌ ERROR: Insufficient memory to generate large datasets",
            file=sys.stderr,
        )
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}", exc_info=True)
        print(f"\n❌ ERROR: Unexpected error during execution: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
