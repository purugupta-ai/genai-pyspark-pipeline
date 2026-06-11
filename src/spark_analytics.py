from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, round as spark_round, sum as spark_sum
from src.config import (
    setup_logging,
    CUSTOMERS_PARQUET,
    PRODUCTS_PARQUET,
    ORDERS_PARQUET,
    PROCESSED_DATA_DIR,
)

logger = setup_logging(__name__)

def create_spark_session(app_name: str = "EcommerceAnalytics") -> SparkSession:
    """
    Initializes and returns a PySpark Session.

    Args:
        app_name (str): The name of the Spark application.

    Returns:
        SparkSession: The active Spark session.
    """
    logger.info(f"Initializing Spark Session: {app_name}")
    return SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .getOrCreate()

def load_data(spark: SparkSession, filepath: str) -> DataFrame:
    """
    Loads a data file (Parquet or CSV) into a PySpark DataFrame.

    Args:
        spark (SparkSession): The active Spark session.
        filepath (str): The path to the data file (Parquet or CSV).

    Returns:
        DataFrame: A PySpark DataFrame containing the loaded data.
    """
    logger.info(f"Loading data from {filepath}")
    filepath_str = str(filepath).lower()
    
    if filepath_str.endswith(".parquet"):
        return spark.read.parquet(filepath)
    else:
        return spark.read.csv(filepath, header=True, inferSchema=True)

def analyze_sales_by_category(orders_df: DataFrame, products_df: DataFrame) -> DataFrame:
    """
    Analyzes total sales revenue grouped by product category.

    Args:
        orders_df (DataFrame): DataFrame containing order data.
        products_df (DataFrame): DataFrame containing product data.

    Returns:
        DataFrame: A PySpark DataFrame with category and total_revenue.
    """
    logger.info("Performing sales by category analysis...")
    
    # Join orders and products
    joined_df = orders_df.join(products_df, on="product_id", how="inner")
    
    # Calculate revenue (price * quantity) and group by category
    sales_df = joined_df.withColumn("revenue", col("price") * col("quantity")) \
        .groupBy("category") \
        .agg(spark_round(spark_sum("revenue"), 2).alias("total_revenue")) \
        .orderBy(col("total_revenue").desc())
        
    return sales_df

def save_results(df: DataFrame, output_dir: str, filename: str) -> None:
    """
    Saves a DataFrame to the specified output directory as a CSV.

    Args:
        df (DataFrame): The PySpark DataFrame to save.
        output_dir (str): The base processed directory path.
        filename (str): The name of the output folder/file.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = str(output_dir / filename)
    
    logger.info(f"Saving analysis results to {out_path}")
    # Coalesce to 1 partition to get a single CSV file output for this small dataset
    df.coalesce(1).write.mode("overwrite").csv(out_path, header=True)

def main() -> None:
    """Main execution function to run the PySpark analytics pipeline."""
    logger.info("Starting PySpark Analytics Pipeline")
    
    spark = create_spark_session()
    
    try:
        # Load Raw Data (from Parquet files)
        orders_df = load_data(spark, ORDERS_PARQUET)
        products_df = load_data(spark, PRODUCTS_PARQUET)
        
        # Analyze Data
        category_sales_df = analyze_sales_by_category(orders_df, products_df)
        
        # Show sample in console for debugging
        logger.info("Top 5 Categories by Revenue:")
        category_sales_df.show(5)
        
        # Save Data
        save_results(category_sales_df, PROCESSED_DATA_DIR, "sales_by_category")
        
    except Exception as e:
        logger.error(f"An error occurred during PySpark execution: {str(e)}")
    finally:
        logger.info("Stopping Spark Session")
        spark.stop()

if __name__ == "__main__":
    main()