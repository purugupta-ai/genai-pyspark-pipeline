"""
PySpark Analytics Module for E-Commerce Data Analysis.

This module provides a SalesAnalytics class for performing advanced analytics on
e-commerce data including customer revenue analysis, category trends, and growth metrics.
"""

import logging
from pathlib import Path
from typing import Optional

from pyspark.sql import SparkSession, Window, DataFrame
from pyspark.sql.functions import (
    col,
    sum as spark_sum,
    count as spark_count,
    round as spark_round,
    date_format,
    year,
    month,
    lag,
)

from src.config import (
    setup_logging,
    CUSTOMERS_PARQUET,
    PRODUCTS_PARQUET,
    ORDERS_PARQUET,
    PROCESSED_DATA_DIR,
)
from src.spark_config import SparkOptimizedConfig

logger = setup_logging(__name__)


class SalesAnalytics:
    """
    Comprehensive PySpark analytics class for e-commerce data analysis.
    
    Provides methods for:
    - Loading Parquet files into Spark DataFrames
    - Analyzing top customers by revenue
    - Calculating sales by product category
    - Computing month-over-month revenue growth trends
    
    Features:
    - Optimized Spark configuration (4GB memory, Kryo serialization)
    - Adaptive Query Execution (AQE) enabled
    - Proper resource management with context managers
    
    Attributes:
        spark (SparkSession): Active Spark session
        is_active (bool): Whether the session is currently active
    """
    
    def __init__(self):
        """Initialize SalesAnalytics."""
        self.spark: Optional[SparkSession] = None
        self.is_active: bool = False
        logger.info("Initialized SalesAnalytics")
    
    def create_spark_session(self, app_name: str = "SalesAnalytics") -> SparkSession:
        """
        Create and configure a Spark session with optimized settings for 8GB/2-core systems.
        
        Uses SparkOptimizedConfig for all settings:
        - Driver Memory: 4GB (coordinates work, collects results)
        - Executor Memory: 2GB (actual computation)
        - Shuffle Partitions: 16 (optimized for 2 cores, not default 200)
        - Serializer: Kryo (2-10x faster than Java)
        - Adaptive Query Execution: Enabled (handles data skew automatically)
        
        Configuration Details:
        1. spark.driver.memory = 4GB (50% of 8GB system)
        2. spark.sql.shuffle.partitions = 16 (2 cores × 8)
        3. spark.sql.adaptive.enabled = True (auto-optimization)
        4. spark.serializer = KryoSerializer (fast binary serialization)
        5. spark.sql.adaptive.coalescePartitions.enabled = True (merge small partitions)
        
        Why these values?
        - 4GB driver handles 1M orders + aggregations + results collection
        - 16 partitions prevent memory overhead from 200 default partitions
        - Kryo reduces serialization time when shuffling data
        - AQE detects skewed customers (customer 100000 with 353K orders)
        
        Args:
            app_name (str): Name of the Spark application. Default: "SalesAnalytics"
            
        Returns:
            SparkSession: Fully configured Spark session ready for analytics
        """
        logger.info(f"Creating optimized Spark session: {app_name}")
        
        # Use optimized configuration from spark_config.py
        self.spark = SparkOptimizedConfig.create_optimized_session(app_name)
        self.is_active = True
        
        return self.spark
    
    def load_parquet(self, filepath: Path) -> DataFrame:
        """
        Load a Parquet file into a Spark DataFrame.
        
        Args:
            filepath (Path): Path to the Parquet file
            
        Returns:
            DataFrame: Spark DataFrame containing the data
            
        Raises:
            FileNotFoundError: If file does not exist
            Exception: If Parquet read fails
        """
        if not self.spark:
            raise RuntimeError("Spark session not initialized. Call create_spark_session() first.")
        
        filepath_str = str(filepath)
        logger.info(f"Loading Parquet file: {filepath_str}")
        
        if not Path(filepath_str).exists():
            raise FileNotFoundError(f"File not found: {filepath_str}")
        
        try:
            df = self.spark.read.parquet(filepath_str)
            logger.info(f"Loaded {df.count():,} rows from {filepath_str}")
            return df
        except Exception as e:
            logger.error(f"Failed to load Parquet file: {e}")
            raise
    
    def top_customers_by_revenue(
        self,
        orders_df: DataFrame,
        products_df: DataFrame,
        n: int = 10,
    ) -> DataFrame:
        """
        Find top N customers by total revenue spent.
        
        Joins orders with products, calculates total spend per customer,
        and returns the top N customers ranked by revenue.
        
        Args:
            orders_df (DataFrame): Orders data with columns:
                [order_id, customer_id, product_id, quantity, order_date]
            products_df (DataFrame): Products data with columns:
                [product_id, name, category, price, stock, rating]
            n (int): Number of top customers to return. Default: 10
            
        Returns:
            DataFrame: Top N customers with columns:
                [customer_id, total_revenue, order_count]
        """
        logger.info(f"Calculating top {n} customers by revenue...")
        
        # Join orders with products on product_id
        joined_df = (
            orders_df.join(products_df, on="product_id", how="inner")
            .withColumn("revenue", col("price") * col("quantity"))
        )
        
        # Group by customer and aggregate
        top_customers = (
            joined_df
            .groupBy("customer_id")
            .agg(
                spark_round(spark_sum("revenue"), 2).alias("total_revenue"),
                spark_count("order_id").alias("order_count"),
            )
            .orderBy(col("total_revenue").desc())
            .limit(n)
        )
        
        logger.info(f"Calculated top {n} customers by revenue")
        return top_customers
    
    def sales_by_category(
        self,
        orders_df: DataFrame,
        products_df: DataFrame,
    ) -> DataFrame:
        """
        Analyze total sales revenue and units sold by product category.
        
        Groups orders by product category and calculates:
        - Total revenue (price * quantity)
        - Total units sold
        - Number of orders
        - Average order value per category
        
        Args:
            orders_df (DataFrame): Orders data with columns:
                [order_id, customer_id, product_id, quantity, order_date]
            products_df (DataFrame): Products data with columns:
                [product_id, name, category, price, stock, rating]
            
        Returns:
            DataFrame: Sales by category with columns:
                [category, total_revenue, total_units, order_count, avg_order_value]
        """
        logger.info("Analyzing sales by category...")
        
        # Join orders with products
        joined_df = (
            orders_df.join(products_df, on="product_id", how="inner")
            .withColumn("revenue", col("price") * col("quantity"))
        )
        
        # Group by category and aggregate
        category_sales = (
            joined_df
            .groupBy("category")
            .agg(
                spark_round(spark_sum("revenue"), 2).alias("total_revenue"),
                spark_sum("quantity").alias("total_units"),
                spark_count("order_id").alias("order_count"),
            )
            .withColumn(
                "avg_order_value",
                spark_round(col("total_revenue") / col("order_count"), 2),
            )
            .orderBy(col("total_revenue").desc())
        )
        
        logger.info("Calculated sales by category")
        return category_sales
    
    def monthly_trends(
        self,
        orders_df: DataFrame,
        products_df: DataFrame,
    ) -> DataFrame:
        """
        Calculate month-over-month revenue growth trends.
        
        Groups orders by month, calculates monthly revenue, and computes
        month-over-month growth percentage using Window functions.
        
        Args:
            orders_df (DataFrame): Orders data with columns:
                [order_id, customer_id, product_id, quantity, order_date]
            products_df (DataFrame): Products data with columns:
                [product_id, name, category, price, stock, rating]
            
        Returns:
            DataFrame: Monthly trends with columns:
                [year, month, month_date, monthly_revenue, prev_month_revenue, growth_percent]
        """
        logger.info("Calculating monthly revenue trends...")
        
        # Join orders with products
        joined_df = (
            orders_df.join(products_df, on="product_id", how="inner")
            .withColumn("revenue", col("price") * col("quantity"))
        )
        
        # Extract year and month, create month_date for sorting
        monthly_data = (
            joined_df
            .withColumn("year", year("order_date"))
            .withColumn("month", month("order_date"))
            .withColumn(
                "month_date",
                date_format("order_date", "yyyy-MM-01")
            )
        )
        
        # Group by month and calculate monthly revenue
        monthly_revenue = (
            monthly_data
            .groupBy("year", "month", "month_date")
            .agg(
                spark_round(spark_sum("revenue"), 2).alias("monthly_revenue"),
            )
            .orderBy("year", "month")
        )
        
        # Define window for calculating growth
        window_spec = Window.orderBy("year", "month")
        
        # Calculate previous month's revenue and growth percentage
        monthly_trends_with_growth = (
            monthly_revenue
            .withColumn(
                "prev_month_revenue",
                lag("monthly_revenue").over(window_spec),
            )
            .withColumn(
                "growth_percent",
                spark_round(
                    ((col("monthly_revenue") - col("prev_month_revenue"))
                     / col("prev_month_revenue")) * 100,
                    2,
                ),
            )
        )
        
        logger.info("Calculated monthly revenue trends with growth rates")
        return monthly_trends_with_growth
    
    def save_results(
        self,
        df: DataFrame,
        output_name: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Save a DataFrame to a Parquet file in the processed directory.
        
        Uses Parquet format for better performance and compatibility.
        
        Args:
            df (DataFrame): Spark DataFrame to save
            output_name (str): Name of the output file (without extension)
            output_dir (Path): Output directory. Default: PROCESSED_DATA_DIR
            
        Returns:
            Path: Path where the file was saved
        """
        if output_dir is None:
            output_dir = PROCESSED_DATA_DIR
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_name
        
        logger.info(f"Saving results to {output_path}")
        
        # Save as Parquet (better performance and Windows compatibility)
        df.write.mode("overwrite").parquet(str(output_path))
        
        logger.info(f"Results saved to {output_path}")
        return output_path
    
    def stop_session(self) -> None:
        """
        Stop the Spark session and clean up resources.
        """
        if self.spark and self.is_active:
            logger.info("Stopping Spark session")
            self.spark.stop()
            self.is_active = False
            logger.info("Spark session stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.create_spark_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_session()


def main() -> None:
    """
    Main execution function to run the complete PySpark analytics pipeline.
    
    Demonstrates:
    - Loading Parquet files
    - Analyzing top customers by revenue
    - Calculating sales by category
    - Computing monthly trends with growth rates
    - Saving results
    """
    logger.info("=" * 70)
    logger.info("STARTING PYSPARK ANALYTICS PIPELINE")
    logger.info("=" * 70)
    
    # Use context manager for automatic resource cleanup
    with SalesAnalytics() as analytics:
        try:
            # Load data
            logger.info("\nLoading data files...")
            orders_df = analytics.load_parquet(ORDERS_PARQUET)
            products_df = analytics.load_parquet(PRODUCTS_PARQUET)
            
            # Display schemas
            logger.info("\n--- Orders Schema ---")
            orders_df.printSchema()
            logger.info("\n--- Products Schema ---")
            products_df.printSchema()
            
            # Analysis 1: Top Customers by Revenue
            logger.info("\n" + "=" * 70)
            logger.info("ANALYSIS 1: TOP 10 CUSTOMERS BY REVENUE")
            logger.info("=" * 70)
            top_customers = analytics.top_customers_by_revenue(
                orders_df, products_df, n=10
            )
            top_customers.show(10)
            analytics.save_results(top_customers, "top_customers_by_revenue")
            
            # Analysis 2: Sales by Category
            logger.info("\n" + "=" * 70)
            logger.info("ANALYSIS 2: SALES BY CATEGORY")
            logger.info("=" * 70)
            category_sales = analytics.sales_by_category(orders_df, products_df)
            category_sales.show()
            analytics.save_results(category_sales, "sales_by_category")
            
            # Analysis 3: Monthly Trends
            logger.info("\n" + "=" * 70)
            logger.info("ANALYSIS 3: MONTHLY REVENUE TRENDS")
            logger.info("=" * 70)
            monthly_trends = analytics.monthly_trends(orders_df, products_df)
            monthly_trends.show(20)
            analytics.save_results(monthly_trends, "monthly_revenue_trends")
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ ANALYTICS PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Error during analytics pipeline: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    main()