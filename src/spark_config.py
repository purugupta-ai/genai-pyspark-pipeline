"""
Optimized PySpark Configuration for 8GB RAM / 2-Core Laptop
Processing 1 Million E-Commerce Orders

System Specs:
- RAM: 8 GB total
- CPU Cores: 2
- Data Volume: 1 million orders
- Optimization Goal: Balance memory, parallelism, and speed
"""

from pyspark.sql import SparkSession
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SparkOptimizedConfig:
    """
    Configuration class for optimized Spark session on resource-constrained systems.
    
    HARDWARE ALLOCATION STRATEGY:
    ============================
    Total RAM: 8 GB
    - Driver Memory: 4 GB (50% - handles data collection & coordination)
    - Executor Memory: 2 GB (25% - actual computation)
    - System/OS: 2 GB (25% - operating system overhead)
    
    CPU CORES: 2
    - Parallelism tasks: 2 (one per core, no oversubscription)
    - Shuffle partitions: 16-32 (optimize for small number of cores)
    """
    
    # ============================================================================
    # 1. DRIVER MEMORY CONFIGURATION
    # ============================================================================
    # spark.driver.memory: Amount of memory to allocate to Spark driver process
    # 
    # CALCULATION:
    #   - Total RAM: 8 GB
    #   - OS/System reserve: 2 GB
    #   - Available for Spark: 6 GB
    #   - Driver allocation: 4 GB (largest component as it coordinates work)
    #   - Executor allocation: 2 GB (computation tasks)
    #
    # WHY 4GB for Driver?
    #   • Collects aggregated results from executors
    #   • Manages task scheduling and coordination
    #   • Holds metadata for 1M orders (customer info, product details)
    #   • Buffer for sorting/grouping operations
    #
    # IMPACT of wrong value:
    #   - Too low (<2GB): OutOfMemoryError when collecting results
    #   - Too high (>5GB): System swapping, reduced OS availability
    DRIVER_MEMORY = "4G"
    
    # ============================================================================
    # 2. EXECUTOR MEMORY CONFIGURATION
    # ============================================================================
    # spark.executor.memory: RAM per executor task
    # 
    # With 2 cores, we have 2 executors (one per core)
    # Each executor gets 2GB for actual computation
    EXECUTOR_MEMORY = "2G"
    
    # ============================================================================
    # 3. SHUFFLE PARTITIONS OPTIMIZATION
    # ============================================================================
    # spark.sql.shuffle.partitions: Number of partitions for groupBy, join operations
    #
    # DEFAULT: 200 (designed for clusters with many cores)
    # LAPTOP OPTIMIZED: 16
    #
    # WHY 16 partitions for 2 cores?
    #   • Rule of thumb: 2-8x number of cores
    #   • 2 cores × 8 = 16 partitions
    #   • Creates enough parallelism without excessive overhead
    #   • Reduces memory pressure per partition
    #
    # IMPACT on aggregations:
    #   - Too low (4): Underutilizes CPU, long processing time
    #   - Default 200: Excessive memory overhead, swapping on 8GB RAM
    #   - Optimal 16: Balanced parallelism and memory
    #
    # USE CASES:
    #   • top_customers_by_revenue(): GROUP BY customer_id (benefits from 16 partitions)
    #   • sales_by_category(): GROUP BY category (5 categories, 16 partitions ideal)
    #   • monthly_trends(): GROUP BY year, month (24 months, 16 partitions sufficient)
    SHUFFLE_PARTITIONS = 16
    
    # ============================================================================
    # 4. SERIALIZER CONFIGURATION (Kryo vs Java)
    # ============================================================================
    # spark.serializer: Algorithm for serializing objects between driver/executors
    #
    # OPTIONS:
    #   • org.apache.spark.serializer.JavaSerializer (default): Slow, verbose
    #   • org.apache.spark.serializer.KryoSerializer (optimized): 2-10x faster
    #
    # WHY KRYO?
    #   • Smaller serialized size → less network traffic
    #   • Faster serialization/deserialization
    #   • Crucial for 2-core system with frequent shuffle operations
    #   • 1M orders = massive data movement between driver/executors
    #
    # KRYO PERFORMANCE METRICS:
    #   • Serialization speed: ~10x faster than Java
    #   • Data size reduction: 30-50% smaller
    #   • Especially beneficial for complex data types (DataFrames, custom objects)
    #
    # EXAMPLE: 1M orders shuffled
    #   - Java Serializer: Large byte arrays, slow I/O
    #   - Kryo: Compact binary format, instant I/O
    SERIALIZER = "org.apache.spark.serializer.KryoSerializer"
    
    # Kryo registration buffer size (for complex object graphs)
    KRYO_BUFFER_SIZE = "512m"  # Sufficient for our data structures
    
    # ============================================================================
    # 5. ADAPTIVE QUERY EXECUTION (AQE)
    # ============================================================================
    # spark.sql.adaptive.enabled: Enable runtime query optimization
    #
    # WHAT IT DOES:
    #   • Monitors job execution in real-time
    #   • Adjusts execution plan mid-flight based on actual data
    #   • Handles skew in data automatically
    #
    # WHY CRITICAL FOR 1M ORDERS?
    #   • Customer distribution is Pareto-skewed (customer 100000 has 353K orders)
    #   • One partition might have 300K rows while others have 1K
    #   • Without AQE: Slow executor waits for skewed partition
    #   • With AQE: Detects skew, rebalances automatically
    #
    # AQE SUB-FEATURES:
    ADAPTIVE_ENABLED = True
    
    # 5a. Coalesce Partitions
    # spark.sql.adaptive.coalescePartitions.enabled: Merge small partitions
    #
    # SCENARIO:
    #   • Start with 16 partitions
    #   • After shuffle, some have 100 rows, some 100K
    #   • Merging small ones reduces task overhead
    #
    # BENEFIT: Reduces number of tasks from 16 to maybe 4-8
    COALESCE_PARTITIONS_ENABLED = True
    COALESCE_PARTITIONS_MIN_PARTITIONS = 1  # Minimum 1 partition after coalesce
    
    # 5b. Skew Join Detection & Handling
    # spark.sql.adaptive.skewJoin.enabled: Handle uneven join distribution
    #
    # SCENARIO WITH OUR DATA:
    #   • Joining orders (1M) with products (10K)
    #   • Top customer has 353K orders → huge partition
    #   • Skew detection: Identifies this partition
    #   • Solution: Splits large partition, replicates product data
    SKEW_JOIN_ENABLED = True
    SKEW_PARTITION_THRESHOLD = 256 * 1024 * 1024  # 256 MB - flag if partition > 256MB
    
    # ============================================================================
    # 6. MEMORY MANAGEMENT
    # ============================================================================
    # spark.memory.fraction: How much executor memory for caching vs shuffle
    # Default: 0.6 (60% for caching, 40% for shuffle operations)
    # We reduce caching since 1M rows fits in 2GB with minimal caching
    MEMORY_FRACTION = 0.5  # 50% caching, 50% shuffle (better balance)
    
    # ============================================================================
    # 7. TASK & PARTITION OPTIMIZATION
    # ============================================================================
    # spark.default.parallelism: Number of partitions for RDD operations
    DEFAULT_PARALLELISM = 16  # Matches shuffle.partitions
    
    # spark.sql.files.maxPartitionBytes: Max bytes per partition when reading
    # Prevents creating too many partitions from 1M order Parquet file
    MAX_PARTITION_BYTES = 128 * 1024 * 1024  # 128 MB per partition
    
    # ============================================================================
    # 8. NETWORK & I/O OPTIMIZATION
    # ============================================================================
    # spark.reducer.maxSizeInFlight: Max data per reducer before spilling to disk
    # With 2GB executor memory, be conservative
    REDUCER_MAX_SIZE_IN_FLIGHT = 128 * 1024 * 1024  # 128 MB
    
    # spark.shuffle.compress: Compress shuffle data (saves I/O)
    SHUFFLE_COMPRESS = True
    
    # spark.shuffle.spill.compress: Compress data spilled to disk
    SHUFFLE_SPILL_COMPRESS = True
    
    # ============================================================================
    # 9. LOGGING & DEBUGGING
    # ============================================================================
    LOG_LEVEL = "WARN"  # Reduce noise, show only warnings/errors
    
    @staticmethod
    def create_optimized_session(app_name: str = "OptimizedAnalytics") -> SparkSession:
        """
        Create SparkSession with all optimizations applied.
        
        Args:
            app_name: Name of the Spark application
            
        Returns:
            Configured SparkSession ready for 1M order processing
            
        Example:
            >>> spark = SparkOptimizedConfig.create_optimized_session("MyApp")
            >>> spark.sql("SELECT * FROM my_table").show()
        """
        logger.info("Creating optimized Spark session for 8GB/2-core system...")
        
        spark = (
            SparkSession.builder
            # Basic configuration
            .appName(app_name)
            .master("local[2]")  # Use both CPU cores
            
            # ================================================================
            # MEMORY CONFIGURATION (1. & 2.)
            # ================================================================
            .config("spark.driver.memory", SparkOptimizedConfig.DRIVER_MEMORY)
            .config("spark.executor.memory", SparkOptimizedConfig.EXECUTOR_MEMORY)
            .config("spark.memory.fraction", SparkOptimizedConfig.MEMORY_FRACTION)
            
            # ================================================================
            # SERIALIZATION (4.)
            # ================================================================
            .config("spark.serializer", SparkOptimizedConfig.SERIALIZER)
            .config("spark.kryoserializer.buffer.max", SparkOptimizedConfig.KRYO_BUFFER_SIZE)
            
            # ================================================================
            # SHUFFLE & PARTITIONING (3. & 7.)
            # ================================================================
            .config("spark.sql.shuffle.partitions", SparkOptimizedConfig.SHUFFLE_PARTITIONS)
            .config("spark.default.parallelism", SparkOptimizedConfig.DEFAULT_PARALLELISM)
            .config("spark.sql.files.maxPartitionBytes", SparkOptimizedConfig.MAX_PARTITION_BYTES)
            
            # ================================================================
            # ADAPTIVE QUERY EXECUTION (5.)
            # ================================================================
            .config("spark.sql.adaptive.enabled", SparkOptimizedConfig.ADAPTIVE_ENABLED)
            .config("spark.sql.adaptive.coalescePartitions.enabled", 
                   SparkOptimizedConfig.COALESCE_PARTITIONS_ENABLED)
            .config("spark.sql.adaptive.coalescePartitions.minPartitions",
                   SparkOptimizedConfig.COALESCE_PARTITIONS_MIN_PARTITIONS)
            .config("spark.sql.adaptive.skewJoin.enabled", SparkOptimizedConfig.SKEW_JOIN_ENABLED)
            .config("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes",
                   SparkOptimizedConfig.SKEW_PARTITION_THRESHOLD)
            
            # ================================================================
            # NETWORK & I/O (8.)
            # ================================================================
            .config("spark.reducer.maxSizeInFlight", SparkOptimizedConfig.REDUCER_MAX_SIZE_IN_FLIGHT)
            .config("spark.shuffle.compress", SparkOptimizedConfig.SHUFFLE_COMPRESS)
            .config("spark.shuffle.spill.compress", SparkOptimizedConfig.SHUFFLE_SPILL_COMPRESS)
            
            # ================================================================
            # LOGGING (9.)
            # ================================================================
            .config("spark.sql.adaptive.logLevel", SparkOptimizedConfig.LOG_LEVEL)
        )
        
        session = spark.getOrCreate()
        
        # Log configuration summary
        logger.info("\n" + "="*70)
        logger.info("SPARK SESSION OPTIMIZED CONFIGURATION")
        logger.info("="*70)
        logger.info(f"Driver Memory: {SparkOptimizedConfig.DRIVER_MEMORY}")
        logger.info(f"Executor Memory: {SparkOptimizedConfig.EXECUTOR_MEMORY}")
        logger.info(f"Shuffle Partitions: {SparkOptimizedConfig.SHUFFLE_PARTITIONS}")
        logger.info(f"Serializer: Kryo (optimized)")
        logger.info(f"AQE Enabled: {SparkOptimizedConfig.ADAPTIVE_ENABLED}")
        logger.info(f"  - Coalesce Partitions: {SparkOptimizedConfig.COALESCE_PARTITIONS_ENABLED}")
        logger.info(f"  - Skew Join Detection: {SparkOptimizedConfig.SKEW_JOIN_ENABLED}")
        logger.info("="*70)
        
        return session


if __name__ == "__main__":
    # Example usage
    spark = SparkOptimizedConfig.create_optimized_session("TestOptimization")
    print(spark.sparkContext.getConf().getAll())
    spark.stop()
