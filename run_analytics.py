import logging
from pathlib import Path
from time import time

from src.spark_analytics import SalesAnalytics
from src.config import setup_logging, CUSTOMERS_PARQUET, PRODUCTS_PARQUET, ORDERS_PARQUET

# Setup logging
logger = setup_logging(__name__)


def main():
    """Run all analytics operations and display results with execution times."""
    # Pre-flight check: Ensure data files exist
    missing_files = [f for f in [CUSTOMERS_PARQUET, PRODUCTS_PARQUET, ORDERS_PARQUET] if not f.exists()]
    if missing_files:
        logger.error("Missing raw data files in data/raw/")
        for f in missing_files:
            logger.error(f"  - NOT FOUND: {f.name}")
        print("\n[!] Error: Raw data not found. Please run 'python main.py' first to generate datasets.\n")
        return

    analytics = SalesAnalytics()
    try:
        # Create Spark session
        logger.info("Creating Spark session...")
        analytics.create_spark_session(app_name="SalesAnalyticsRunner")
        logger.info("[OK] Spark session created successfully")
        
        # Load data
        logger.info("\nLoading Parquet files from data/raw/...")
        customers_df = analytics.load_parquet(CUSTOMERS_PARQUET)
        products_df = analytics.load_parquet(PRODUCTS_PARQUET)
        orders_df = analytics.load_parquet(ORDERS_PARQUET)
        logger.info("[OK] All data loaded successfully")
        
        # Analysis 1: Top Customers by Revenue
        logger.info("\n" + "="*70)
        logger.info("ANALYSIS 1: Top Customers by Revenue")
        logger.info("="*70)
        start_time = time()
        top_customers = analytics.top_customers_by_revenue(orders_df, products_df, n=10)
        execution_time = time() - start_time
        analytics.save_results(top_customers, "top_customers_by_revenue")
        print(f"\n[TIME] Execution Time: {execution_time:.2f} seconds\n")
        top_customers.show(truncate=False)
        
        # Analysis 2: Sales by Category
        logger.info("\n" + "="*70)
        logger.info("ANALYSIS 2: Sales by Category")
        logger.info("="*70)
        start_time = time()
        sales_by_cat = analytics.sales_by_category(orders_df, products_df)
        execution_time = time() - start_time
        analytics.save_results(sales_by_cat, "sales_by_category")
        print(f"\n[TIME] Execution Time: {execution_time:.2f} seconds\n")
        sales_by_cat.show(truncate=False)
        
        # Analysis 3: Monthly Trends
        logger.info("\n" + "="*70)
        logger.info("ANALYSIS 3: Monthly Trends")
        logger.info("="*70)
        start_time = time()
        monthly = analytics.monthly_trends(orders_df, products_df)
        execution_time = time() - start_time
        analytics.save_results(monthly, "monthly_revenue_trends")
        print(f"\n[TIME] Execution Time: {execution_time:.2f} seconds\n")
        monthly.show(n=24, truncate=False)
        
        logger.info("\n" + "="*70)
        logger.info("[SUCCESS] All analyses completed successfully!")
        logger.info("="*70)
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during analytics execution: {e}", exc_info=True)
        raise
    finally:
        # Stop Spark session
        if analytics.is_active:
            logger.info("\nStopping Spark session...")
            analytics.stop_session()
            logger.info("[OK] Spark session stopped")


if __name__ == "__main__":
    main()
