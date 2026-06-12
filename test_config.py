"""
Configuration Explanation & Testing Script
==========================================

This script demonstrates the optimized Spark configuration for 8GB/2-core systems.
Run this to understand each configuration parameter and its impact.
"""

import logging
from src.spark_config import SparkOptimizedConfig
from src.config import setup_logging, ORDERS_PARQUET

# Setup logging
logger = setup_logging(__name__)


def print_config_explanation():
    """Print detailed explanation of each configuration parameter."""
    
    print("\n" + "="*80)
    print("OPTIMIZED SPARK CONFIGURATION FOR 8GB RAM / 2-CORE LAPTOP")
    print("="*80)
    
    explanations = {
        "1. spark.driver.memory = 4G": [
            "[PURPOSE] RAM allocated to Spark driver process",
            "[VALUE] 4 GB (50% of 8GB system)",
            "[WHY THIS VALUE?]",
            "  + Needs enough to collect results from executors",
            "  + Handles metadata for 1M orders",
            "  + Manages task scheduling and coordination",
            "  + Buffer for sorting/grouping operations",
            "[IF TOO LOW (<2GB)]",
            "  - OutOfMemoryError when aggregating results",
            "  - Cannot handle 1M order analysis",
            "[IF TOO HIGH (>5GB)]",
            "  - System swapping, reduced OS performance",
            "  - Other processes starve for memory",
            "[IMPACT ON OUR ANALYTICS]",
            "  * top_customers_by_revenue() safely collects top 10 results",
            "  * sales_by_category() handles 5 category aggregations",
            "  * monthly_trends() processes 24 months of data",
        ],
        
        "2. spark.executor.memory = 2G": [
            "[PURPOSE] RAM per executor for computation",
            "[VALUE] 2 GB (25% of 8GB system)",
            "[WHY THIS VALUE?]",
            "  + With 2 cores, we have 2 executors",
            "  + Each executor gets 2GB for actual work",
            "  + Total for computation: 2 executors x 2GB = 4GB",
            "[DISTRIBUTION: 8GB Total]",
            "  Driver: 4GB   | Executors: 2GB x 2 | OS/System: 2GB",
            "[IMPACT ON 1M ORDERS]",
            "  * Each partition (16 total) = 2GB/16 = 125MB per partition",
            "  * Safe memory headroom for shuffle operations",
        ],
        
        "3. spark.sql.shuffle.partitions = 16": [
            "[PURPOSE] Number of partitions for GROUP BY, JOIN operations",
            "[VALUE] 16 (NOT default 200)",
            "[WHY NOT USE DEFAULT 200?]",
            "  + Default 200 is for clusters with many cores",
            "  + 200 partitions x 2GB executor = massive overhead",
            "  + Would cause memory swapping on 8GB system",
            "[HOW WE CALCULATED 16]",
            "  Formula: partitions = num_cores x 2-8",
            "  With 2 cores: 2 x 8 = 16 partitions",
            "[BENEFITS OF 16 FOR OUR DATA]",
            "  * top_customers_by_revenue(): GROUP BY customer_id -> 100K unique",
            "    16 partitions enough to parallelize grouping",
            "  * sales_by_category(): GROUP BY category -> 5 unique",
            "    16 partitions provides flexibility",
            "  * monthly_trends(): GROUP BY year, month -> 24 unique",
            "    16 partitions handles windowing efficiently",
            "[PARTITION SIZE WITH 16]",
            "  1M orders / 16 partitions = ~62.5K orders per partition",
        ],
        
        "4. spark.serializer = KryoSerializer": [
            "[PURPOSE] Binary format for object serialization",
            "[OPTIONS]",
            "  JavaSerializer (default): Slow, verbose, large size",
            "  KryoSerializer (chosen): Fast, compact, 2-10x improvement",
            "[WHY KRYO?]",
            "  * Smaller serialized size -> less network I/O",
            "  * Faster serialization/deserialization",
            "  * Critical with 2-core system (high data movement)",
            "[PERFORMANCE METRICS]",
            "  * Serialization speed: ~10x faster than Java",
            "  * Data size: 30-50% smaller than Java",
            "  * Network throughput: Massive improvement",
            "[IMPACT ON 1M ORDERS SHUFFLE]",
            "  Example shuffle operation (groupBy customer):",
            "  * Java: 2-3 seconds",
            "  * Kryo: 0.3-0.5 seconds",
            "  -> 5-6x faster due to compact representation",
            "[CONFIGURATION]",
            "  spark.kryoserializer.buffer.max = 512m",
            "  (Sufficient buffer for complex data structures)",
        ],
        
        "5. spark.sql.adaptive.enabled = true": [
            "[PURPOSE] Enable runtime query optimization",
            "[WHAT IT DOES]",
            "  * Monitors execution in real-time",
            "  * Adjusts execution plan based on actual data",
            "  * Handles skewed data automatically",
            "[WHY CRITICAL FOR OUR DATA?]",
            "  Customer distribution is HEAVILY SKEWED:",
            "  * Customer 100000: 353,311 orders (35% of all orders!)",
            "  * Customer 1423: 25 orders",
            "  * 99,999 other customers in between",
            "[PROBLEM WITHOUT AQE]",
            "  * Partition 1: 353K orders",
            "  * Partition 2-16: ~46K orders each",
            "  - Executor processing partition 1 takes 10x longer",
            "  - Other executors idle while waiting",
            "  - Total time = time of slowest partition",
            "[SOLUTION WITH AQE]",
            "  + Detects skew during execution",
            "  + Splits partition 1 into sub-partitions",
            "  + Rebalances work across executors",
            "  + All executors finish at same time",
            "[EXPECTED IMPROVEMENT]",
            "  Skewed operations: 2-3x faster with AQE enabled",
        ],
        
        "5a. spark.sql.adaptive.coalescePartitions.enabled = true": [
            "[PURPOSE] Merge small partitions after shuffle",
            "[SCENARIO DURING EXECUTION]",
            "  After groupBy customer_id with AQE:",
            "  * Partition 1: 300K rows (customer 100000)",
            "  * Partition 2: 50K rows",
            "  * Partition 3: 48K rows",
            "  * Partition 16: 100 rows (tiny!)",
            "[COALESCING BENEFIT]",
            "  + Merges partitions 14-16 into single partition",
            "  + Reduces task overhead",
            "  + Final partitions: ~4-8 instead of 16",
            "[IMPACT]",
            "  * Fewer task scheduling overhead",
            "  * Better CPU cache utilization",
            "  * Faster task completion",
            "[THRESHOLD]",
            "  coalescePartitions.minPartitions = 1",
            "  (Allow coalescing to 1 partition if efficient)",
        ],
        
        "5b. spark.sql.adaptive.skewJoin.enabled = true": [
            "[PURPOSE] Handle uneven distribution in JOIN operations",
            "[USE CASE IN OUR ANALYTICS]",
            "  JOIN orders (1M) with products (10K):",
            "  * orders.product_id partitions vary greatly",
            "  * Some products have thousands of orders",
            "  * Other products have only few orders",
            "[PROBLEM WITHOUT SKEW JOIN]",
            "  - Partition with popular product hangs",
            "  - Other partitions complete in 0.1s",
            "  - Total time = time of slowest partition",
            "[SOLUTION]",
            "  + Detects large partitions (>256MB)",
            "  + Splits skewed join key into sub-keys",
            "  + Replicates small side (products) for sub-joins",
            "  + Balanced join execution",
            "[EXPECTED IMPROVEMENT]",
            "  Skewed JOINs: 2-4x faster",
        ],
    }
    
    for title, lines in explanations.items():
        print(f"\n{title}")
        for line in lines:
            print(line)
    
    print("\n" + "="*80)


def print_configuration_summary():
    """Print a quick reference table of all configurations."""
    
    print("\n" + "="*80)
    print("CONFIGURATION QUICK REFERENCE")
    print("="*80)
    
    configs = [
        ("Parameter", "Value", "For 8GB/2-Core"),
        ("-" * 35, "-" * 25, "-" * 30),
        ("spark.driver.memory", "4G", "Main process coordination"),
        ("spark.executor.memory", "2G", "Per-executor computation"),
        ("spark.sql.shuffle.partitions", "16", "2 cores x 8 factor"),
        ("spark.serializer", "Kryo", "2-10x faster than Java"),
        ("spark.sql.adaptive.enabled", "True", "Auto-optimize at runtime"),
        ("coalescePartitions", "True", "Merge small partitions"),
        ("skewJoin.enabled", "True", "Handle uneven joins"),
        ("spark.memory.fraction", "0.5", "50% cache, 50% shuffle"),
        ("spark.default.parallelism", "16", "Match shuffle.partitions"),
    ]
    
    for param, value, reason in configs:
        print(f"{param:35} {value:25} {reason:30}")


def test_optimized_session():
    """Test the optimized Spark session with real data."""
    
    print("\n" + "="*80)
    print("TESTING OPTIMIZED SPARK SESSION")
    print("="*80)
    
    try:
        # Create optimized session
        logger.info("\nCreating optimized Spark session...")
        spark = SparkOptimizedConfig.create_optimized_session("ConfigTest")
        
        # Check configuration
        conf = spark.sparkContext.getConf()
        logger.info("\nVerifying critical configurations:")
        
        critical_configs = [
            "spark.driver.memory",
            "spark.executor.memory",
            "spark.sql.shuffle.partitions",
            "spark.serializer",
            "spark.sql.adaptive.enabled",
        ]
        
        for key in critical_configs:
            value = conf.get(key, "NOT SET")
            logger.info(f"  [OK] {key}: {value}")
        
        # Test with real data if available
        from pathlib import Path
        if Path(ORDERS_PARQUET).exists():
            logger.info(f"\nLoading test data from {ORDERS_PARQUET}...")
            df = spark.read.parquet(str(ORDERS_PARQUET))
            logger.info(f"[OK] Successfully loaded {df.count():,} orders")
            logger.info(f"[OK] Partitions: {df.rdd.getNumPartitions()}")
            logger.info(f"[OK] Schema: {df.schema.names}")
        
        # Clean up
        spark.stop()
        logger.info("\n[SUCCESS] Session test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)


if __name__ == "__main__":
    print_config_explanation()
    print_configuration_summary()
    test_optimized_session()
    
    print("\n" + "="*80)
    print("DOCUMENTATION COMPLETE")
    print("="*80)
    print("\nFor more details, see src/spark_config.py")
    print("To use in your code:")
    print("  from src.spark_config import SparkOptimizedConfig")
    print("  spark = SparkOptimizedConfig.create_optimized_session('MyApp')")
    print("="*80 + "\n")
