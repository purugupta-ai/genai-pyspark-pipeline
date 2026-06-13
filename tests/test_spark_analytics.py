import pytest
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType
from datetime import date
from src.spark_analytics import SalesAnalytics

@pytest.fixture(scope="module")
def analytics():
    """Fixture to provide SalesAnalytics instance."""
    obj = SalesAnalytics()
    # Manually create a local spark session for testing to avoid overhead of optimized config
    # Using 127.0.0.1 avoids potential network resolution issues on Windows
    obj.spark = (SparkSession.builder
                 .master("local[1]")
                 .appName("UnitTest")
                 .config("spark.driver.host", "127.0.0.1")
                 .config("spark.sql.shuffle.partitions", "1")
                 .config("spark.default.parallelism", "1")
                 .config("spark.sql.warehouse.dir", str(Path("temp_warehouse").absolute()))
                 .getOrCreate())
    obj.is_active = True
    yield obj
    obj.stop_session()

@pytest.fixture
def mock_data(analytics):
    """Provides minimal DataFrames for testing."""
    # Define Schemas
    product_schema = StructType([
        StructField("product_id", IntegerType(), False),
        StructField("name", StringType(), True),
        StructField("category", StringType(), True),
        StructField("price", DoubleType(), True),
    ])
    
    order_schema = StructType([
        StructField("order_id", IntegerType(), False),
        StructField("customer_id", IntegerType(), True),
        StructField("product_id", IntegerType(), True),
        StructField("quantity", IntegerType(), True),
        StructField("order_date", DateType(), True),
    ])

    # Create Data
    products = [
        (1, "Laptop", "Electronics", 1000.0),
        (2, "Shirt", "Clothing", 50.0),
    ]
    
    orders = [
        (101, 1, 1, 1, date(2024, 1, 1)),  # Cust 1, Laptop: 1000
        (102, 1, 2, 2, date(2024, 1, 15)), # Cust 1, Shirt: 100
        (103, 2, 2, 1, date(2024, 2, 1)),  # Cust 2, Shirt: 50
    ]

    products_df = analytics.spark.createDataFrame(products, product_schema)
    orders_df = analytics.spark.createDataFrame(orders, order_schema)
    
    return orders_df, products_df

def test_top_customers_by_revenue(analytics, mock_data):
    """Verify that top customers are ranked correctly by total spend."""
    orders_df, products_df = mock_data
    
    result_df = analytics.top_customers_by_revenue(orders_df, products_df, n=5)
    results = result_df.collect()

    # Customer 1 should have 1100.0 revenue (1000 + 100)
    # Customer 2 should have 50.0 revenue
    assert len(results) == 2
    assert results[0]["customer_id"] == 1
    assert results[0]["total_revenue"] == 1100.0
    assert results[0]["order_count"] == 2
    assert results[1]["customer_id"] == 2
    assert results[1]["total_revenue"] == 50.0

def test_sales_by_category(analytics, mock_data):
    """Verify category aggregation and average order value calculation."""
    orders_df, products_df = mock_data
    
    result_df = analytics.sales_by_category(orders_df, products_df)
    results = {row["category"]: row for row in result_df.collect()}

    assert "Electronics" in results
    assert "Clothing" in results
    
    # Electronics: 1 order, 1000 revenue
    assert results["Electronics"]["total_revenue"] == 1000.0
    assert results["Electronics"]["total_units"] == 1
    
    # Clothing: 2 orders (102, 103), total revenue 150
    assert results["Clothing"]["total_revenue"] == 150.0
    assert results["Clothing"]["order_count"] == 2
    assert results["Clothing"]["avg_order_value"] == 75.0

def test_monthly_trends(analytics, mock_data):
    """Verify growth rate calculation between months."""
    orders_df, products_df = mock_data
    
    result_df = analytics.monthly_trends(orders_df, products_df)
    results = result_df.orderBy("year", "month").collect()

    # Jan 2024 (1100.0) -> Feb 2024 (50.0)
    assert len(results) == 2
    
    jan = results[0]
    feb = results[1]
    
    assert jan["monthly_revenue"] == 1100.0
    assert jan["prev_month_revenue"] is None
    
    assert feb["monthly_revenue"] == 50.0
    assert feb["prev_month_revenue"] == 1100.0
    # Growth: ((50 - 1100) / 1100) * 100 = -95.45%
    assert feb["growth_percent"] == -95.45

def test_load_parquet_file_not_found(analytics):
    """Ensure proper exception handling for missing files."""
    with pytest.raises(FileNotFoundError):
        analytics.load_parquet(Path("non_existent_file.parquet"))

def test_save_results(analytics, mock_data, tmp_path):
    """Verify that results are saved correctly to a temporary path."""
    orders_df, _ = mock_data
    output_name = "test_output"
    
    # Use tmp_path fixture from pytest for safe IO testing
    saved_path = analytics.save_results(orders_df, output_name, output_dir=tmp_path)
    
    assert saved_path.exists()
    assert (tmp_path / output_name).exists()
    
    # Verify data can be read back
    read_back = analytics.spark.read.parquet(saved_path.absolute().as_posix())
    assert read_back.count() == 3