"""
File Format Benchmark with Hardware Metrics.

Benchmarks different file formats (CSV, XLSX, Parquet, ORC, Feather) measuring:
- File size, write/read times, memory usage, CPU time, and energy consumption
"""

import logging
import tracemalloc
import time
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm

from src.config import setup_logging, RAW_DATA_DIR

logger = setup_logging(__name__)


class FileFormatBenchmark:
    """
    Benchmark different file formats with comprehensive hardware metrics.
    
    Measures: file size, write time, read time, peak memory, CPU time, and
    estimated energy consumption for CSV, Parquet, ORC, and Feather formats.
    
    Note: XLSX is excluded due to performance constraints with large datasets.
    
    Attributes:
        num_rows (int): Number of rows in the benchmark DataFrame
        output_dir (Path): Directory to save benchmark files
        cpu_tdp (float): CPU Thermal Design Power in Watts (default: 65W)
        csv_baseline (Dict): Baseline metrics for CSV format (for comparison)
    """
    
    CPU_TDP = 65.0  # Watts - typical CPU TDP
    FORMATS = ["CSV", "Parquet", "Feather"]
    
    def __init__(
        self,
        num_rows: int = 500_000,
        output_dir: Path = None,
        cpu_tdp: float = 65.0,
    ):
        """
        Initialize the benchmark.
        
        Args:
            num_rows (int): Number of rows to generate. Default: 500,000
            output_dir (Path): Directory for output files. Default: RAW_DATA_DIR/benchmarks
            cpu_tdp (float): CPU TDP in Watts. Default: 65W
        """
        self.num_rows = num_rows
        self.output_dir = output_dir or RAW_DATA_DIR / "benchmarks"
        self.cpu_tdp = cpu_tdp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.csv_baseline: Dict = {}
        self.results: Dict[str, Dict] = {}
        
        logger.info(
            f"Initialized FileFormatBenchmark: {num_rows:,} rows, "
            f"output: {self.output_dir}"
        )
    
    def generate_dataframe(self) -> pd.DataFrame:
        """
        Generate a large DataFrame for benchmarking.
        
        Returns:
            pd.DataFrame: DataFrame with 500K rows and 6 columns:
                - id: unique identifier
                - name: person name (Faker)
                - email: email address (Faker)
                - amount: float values (0-10000)
                - date: datetime values (last 365 days)
                - category: categorical values (A-E)
        """
        logger.info(f"Generating benchmark DataFrame with {self.num_rows:,} rows...")
        
        fake = Faker()
        Faker.seed(42)
        np.random.seed(42)
        
        data = {
            "id": range(1, self.num_rows + 1),
            "name": [fake.name() for _ in tqdm(range(self.num_rows), desc="Names", leave=False)],
            "email": [fake.email() for _ in tqdm(range(self.num_rows), desc="Emails", leave=False)],
            "amount": np.random.uniform(10, 10000, self.num_rows),
            "date": pd.date_range(start="2024-01-01", periods=self.num_rows, freq="1min"),
            "category": np.random.choice(["A", "B", "C", "D", "E"], self.num_rows),
        }
        
        df = pd.DataFrame(data)
        logger.info(f"Generated DataFrame shape: {df.shape}")
        return df
    
    def get_file_size_mb(self, filepath: Path) -> float:
        """
        Get file size in MB.
        
        Args:
            filepath (Path): Path to the file
            
        Returns:
            float: File size in MB
        """
        if filepath.exists():
            return filepath.stat().st_size / (1024 * 1024)
        return 0.0
    
    def calculate_energy_consumption(self, cpu_time: float) -> float:
        """
        Calculate estimated energy consumption in Wh (Watt-hours).
        
        Formula: Energy (Wh) = CPU_time (hours) * TDP (Watts)
        
        Args:
            cpu_time (float): CPU time in seconds
            
        Returns:
            float: Energy consumption in Wh
        """
        return (cpu_time / 3600) * self.cpu_tdp
    
    def benchmark_csv(self, df: pd.DataFrame) -> Dict:
        """
        Benchmark CSV format.
        
        Args:
            df (pd.DataFrame): DataFrame to save
            
        Returns:
            Dict: Benchmark metrics
        """
        logger.info("Benchmarking CSV format...")
        filepath = self.output_dir / "benchmark.csv"
        
        metrics = {}
        
        # Write benchmark
        tracemalloc.start()
        write_start_cpu = time.process_time()
        write_start_wall = time.perf_counter()
        
        df.to_csv(filepath, index=False)
        
        write_time_wall = time.perf_counter() - write_start_wall
        write_time_cpu = time.process_time() - write_start_cpu
        _, write_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["write_time"] = write_time_wall
        metrics["write_cpu_time"] = write_time_cpu
        metrics["write_memory"] = write_peak_memory / (1024 * 1024)
        metrics["file_size"] = self.get_file_size_mb(filepath)
        
        # Read benchmark
        tracemalloc.start()
        read_start_cpu = time.process_time()
        read_start_wall = time.perf_counter()
        
        _ = pd.read_csv(filepath)
        
        read_time_wall = time.perf_counter() - read_start_wall
        read_time_cpu = time.process_time() - read_start_cpu
        _, read_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["read_time"] = read_time_wall
        metrics["read_cpu_time"] = read_time_cpu
        metrics["read_memory"] = read_peak_memory / (1024 * 1024)
        metrics["total_cpu_time"] = write_time_cpu + read_time_cpu
        metrics["energy_consumption"] = self.calculate_energy_consumption(
            metrics["total_cpu_time"]
        )
        
        return metrics
    
    def benchmark_xlsx(self, df: pd.DataFrame) -> Dict:
        """
        Benchmark XLSX format.
        
        Note: XLSX is excluded from default benchmarks due to poor performance
        with large datasets. Use for small datasets only (< 10K rows).
        
        Args:
            df (pd.DataFrame): DataFrame to save
            
        Returns:
            Dict: Benchmark metrics
        """
        logger.warning("XLSX benchmarking skipped - too slow for large datasets")
        return {}
    
    def benchmark_parquet(self, df: pd.DataFrame) -> Dict:
        """
        Benchmark Parquet format (using PyArrow).
        
        Args:
            df (pd.DataFrame): DataFrame to save
            
        Returns:
            Dict: Benchmark metrics
        """
        logger.info("Benchmarking Parquet format...")
        filepath = self.output_dir / "benchmark.parquet"
        
        metrics = {}
        
        # Write benchmark
        tracemalloc.start()
        write_start_cpu = time.process_time()
        write_start_wall = time.perf_counter()
        
        df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=False)
        
        write_time_wall = time.perf_counter() - write_start_wall
        write_time_cpu = time.process_time() - write_start_cpu
        _, write_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["write_time"] = write_time_wall
        metrics["write_cpu_time"] = write_time_cpu
        metrics["write_memory"] = write_peak_memory / (1024 * 1024)
        metrics["file_size"] = self.get_file_size_mb(filepath)
        
        # Read benchmark
        tracemalloc.start()
        read_start_cpu = time.process_time()
        read_start_wall = time.perf_counter()
        
        _ = pd.read_parquet(filepath, engine="pyarrow")
        
        read_time_wall = time.perf_counter() - read_start_wall
        read_time_cpu = time.process_time() - read_start_cpu
        _, read_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["read_time"] = read_time_wall
        metrics["read_cpu_time"] = read_time_cpu
        metrics["read_memory"] = read_peak_memory / (1024 * 1024)
        metrics["total_cpu_time"] = write_time_cpu + read_time_cpu
        metrics["energy_consumption"] = self.calculate_energy_consumption(
            metrics["total_cpu_time"]
        )
        
        return metrics
    
    def benchmark_orc(self, df: pd.DataFrame) -> Dict:
        """
        Benchmark ORC format (using PyArrow).
        
        Args:
            df (pd.DataFrame): DataFrame to save
            
        Returns:
            Dict: Benchmark metrics
        """
        logger.info("Benchmarking ORC format...")
        filepath = self.output_dir / "benchmark.orc"
        
        metrics = {}
        
        # Write benchmark
        tracemalloc.start()
        write_start_cpu = time.process_time()
        write_start_wall = time.perf_counter()
        
        df.to_orc(filepath, index=False)
        
        write_time_wall = time.perf_counter() - write_start_wall
        write_time_cpu = time.process_time() - write_start_cpu
        _, write_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["write_time"] = write_time_wall
        metrics["write_cpu_time"] = write_time_cpu
        metrics["write_memory"] = write_peak_memory / (1024 * 1024)
        metrics["file_size"] = self.get_file_size_mb(filepath)
        
        # Read benchmark
        tracemalloc.start()
        read_start_cpu = time.process_time()
        read_start_wall = time.perf_counter()
        
        _ = pd.read_orc(filepath)
        
        read_time_wall = time.perf_counter() - read_start_wall
        read_time_cpu = time.process_time() - read_start_cpu
        _, read_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["read_time"] = read_time_wall
        metrics["read_cpu_time"] = read_time_cpu
        metrics["read_memory"] = read_peak_memory / (1024 * 1024)
        metrics["total_cpu_time"] = write_time_cpu + read_time_cpu
        metrics["energy_consumption"] = self.calculate_energy_consumption(
            metrics["total_cpu_time"]
        )
        
        return metrics
    
    def benchmark_feather(self, df: pd.DataFrame) -> Dict:
        """
        Benchmark Feather format.
        
        Args:
            df (pd.DataFrame): DataFrame to save
            
        Returns:
            Dict: Benchmark metrics
        """
        logger.info("Benchmarking Feather format...")
        filepath = self.output_dir / "benchmark.feather"
        
        metrics = {}
        
        # Write benchmark
        tracemalloc.start()
        write_start_cpu = time.process_time()
        write_start_wall = time.perf_counter()
        
        df.to_feather(filepath)
        
        write_time_wall = time.perf_counter() - write_start_wall
        write_time_cpu = time.process_time() - write_start_cpu
        _, write_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["write_time"] = write_time_wall
        metrics["write_cpu_time"] = write_time_cpu
        metrics["write_memory"] = write_peak_memory / (1024 * 1024)
        metrics["file_size"] = self.get_file_size_mb(filepath)
        
        # Read benchmark
        tracemalloc.start()
        read_start_cpu = time.process_time()
        read_start_wall = time.perf_counter()
        
        _ = pd.read_feather(filepath)
        
        read_time_wall = time.perf_counter() - read_start_wall
        read_time_cpu = time.process_time() - read_start_cpu
        _, read_peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        metrics["read_time"] = read_time_wall
        metrics["read_cpu_time"] = read_time_cpu
        metrics["read_memory"] = read_peak_memory / (1024 * 1024)
        metrics["total_cpu_time"] = write_time_cpu + read_time_cpu
        metrics["energy_consumption"] = self.calculate_energy_consumption(
            metrics["total_cpu_time"]
        )
        
        return metrics
    
    def run_benchmark(self) -> Dict:
        """
        Run benchmarks for all formats.
        
        Returns:
            Dict: Results for all formats with metrics and comparison to CSV baseline
        """
        logger.info("=" * 70)
        logger.info("STARTING FILE FORMAT BENCHMARK")
        logger.info("=" * 70)
        
        # Generate DataFrame
        df = self.generate_dataframe()
        
        # Run benchmarks
        logger.info("\nRunning benchmarks for all formats...")
        self.results["CSV"] = self.benchmark_csv(df)
        self.results["Parquet"] = self.benchmark_parquet(df)
        self.results["Feather"] = self.benchmark_feather(df)
        
        # Set CSV as baseline
        self.csv_baseline = self.results["CSV"].copy()
        
        logger.info("Benchmark completed successfully")
        return self.results
    
    def print_comparison_table(self) -> None:
        """
        Print a formatted comparison table of all metrics across formats.
        
        Shows absolute values and percentage savings vs CSV baseline.
        """
        print("\n" + "=" * 150)
        print("FILE FORMAT BENCHMARK RESULTS - 500,000 Rows")
        print("=" * 150)
        
        # File Size Comparison
        print("\n📊 FILE SIZE (MB):")
        print("-" * 80)
        print(f"{'Format':<15} {'Size (MB)':<15} {'vs CSV':<20}")
        print("-" * 80)
        
        for fmt in self.FORMATS:
            size = self.results[fmt]["file_size"]
            baseline = self.csv_baseline["file_size"]
            pct_change = ((size - baseline) / baseline) * 100
            print(
                f"{fmt:<15} {size:>12.2f}   {pct_change:>15.1f}%"
            )
        
        # Write Time Comparison
        print("\n⏱️  WRITE TIME (seconds):")
        print("-" * 80)
        print(f"{'Format':<15} {'Time (s)':<15} {'vs CSV':<20}")
        print("-" * 80)
        
        for fmt in self.FORMATS:
            write_time = self.results[fmt]["write_time"]
            baseline = self.csv_baseline["write_time"]
            pct_change = ((write_time - baseline) / baseline) * 100
            print(
                f"{fmt:<15} {write_time:>12.3f}   {pct_change:>15.1f}%"
            )
        
        # Read Time Comparison
        print("\n📖 READ TIME (seconds):")
        print("-" * 80)
        print(f"{'Format':<15} {'Time (s)':<15} {'vs CSV':<20}")
        print("-" * 80)
        
        for fmt in self.FORMATS:
            read_time = self.results[fmt]["read_time"]
            baseline = self.csv_baseline["read_time"]
            pct_change = ((read_time - baseline) / baseline) * 100
            print(
                f"{fmt:<15} {read_time:>12.3f}   {pct_change:>15.1f}%"
            )
        
        # Peak Memory Comparison
        print("\n💾 PEAK MEMORY (MB):")
        print("-" * 80)
        print(f"{'Format':<15} {'Write (MB)':<15} {'Read (MB)':<15}")
        print("-" * 80)
        
        for fmt in self.FORMATS:
            write_mem = self.results[fmt]["write_memory"]
            read_mem = self.results[fmt]["read_memory"]
            print(f"{fmt:<15} {write_mem:>12.2f}   {read_mem:>12.2f}")
        
        # CPU Time Comparison
        print("\n⚙️  CPU TIME (seconds):")
        print("-" * 80)
        print(f"{'Format':<15} {'Total CPU (s)':<15} {'vs CSV':<20}")
        print("-" * 80)
        
        for fmt in self.FORMATS:
            cpu_time = self.results[fmt]["total_cpu_time"]
            baseline = self.csv_baseline["total_cpu_time"]
            pct_change = ((cpu_time - baseline) / baseline) * 100
            print(
                f"{fmt:<15} {cpu_time:>12.3f}   {pct_change:>15.1f}%"
            )
        
        # Energy Consumption Comparison
        print("\n⚡ ENERGY CONSUMPTION (Wh) - CPU TDP: 65W:")
        print("-" * 80)
        print(f"{'Format':<15} {'Energy (Wh)':<15} {'vs CSV':<20}")
        print("-" * 80)
        
        for fmt in self.FORMATS:
            energy = self.results[fmt]["energy_consumption"]
            baseline = self.csv_baseline["energy_consumption"]
            pct_change = ((energy - baseline) / baseline) * 100
            print(
                f"{fmt:<15} {energy:>12.6f}   {pct_change:>15.1f}%"
            )
        
        # Summary Ranking
        print("\n🏆 OVERALL PERFORMANCE RANKING:")
        print("-" * 80)
        
        # Score based on file size + write + read time
        scores = {}
        for fmt in self.FORMATS:
            # Normalize metrics (lower is better)
            size_score = self.results[fmt]["file_size"] / self.csv_baseline["file_size"]
            write_score = self.results[fmt]["write_time"] / self.csv_baseline["write_time"]
            read_score = self.results[fmt]["read_time"] / self.csv_baseline["read_time"]
            
            # Weighted score
            scores[fmt] = (size_score * 0.4 + write_score * 0.3 + read_score * 0.3)
        
        ranked = sorted(scores.items(), key=lambda x: x[1])
        for rank, (fmt, score) in enumerate(ranked, 1):
            print(f"{rank}. {fmt:<12} - Score: {score:.3f}")
        
        print("=" * 150 + "\n")
    
    def save_results_to_csv(self, filepath: Path = None) -> None:
        """
        Save benchmark results to a CSV file.
        
        Args:
            filepath (Path): Path to save results. Default: benchmarks/results.csv
        """
        if filepath is None:
            filepath = self.output_dir / "benchmark_results.csv"
        
        # Prepare data for CSV
        results_list = []
        for fmt in self.FORMATS:
            results_list.append({
                "format": fmt,
                "file_size_mb": self.results[fmt]["file_size"],
                "write_time_s": self.results[fmt]["write_time"],
                "read_time_s": self.results[fmt]["read_time"],
                "write_memory_mb": self.results[fmt]["write_memory"],
                "read_memory_mb": self.results[fmt]["read_memory"],
                "total_cpu_time_s": self.results[fmt]["total_cpu_time"],
                "energy_consumption_wh": self.results[fmt]["energy_consumption"],
            })
        
        results_df = pd.DataFrame(results_list)
        results_df.to_csv(filepath, index=False)
        logger.info(f"Results saved to {filepath}")


def main() -> None:
    """Main execution function for the benchmark."""
    logger.info("Starting File Format Benchmark")
    
    # Run benchmark with 500K rows (or adjust for faster execution)
    # Note: XLSX format is slow with large datasets; use 100K rows for quick testing
    num_rows = 500_000
    benchmark = FileFormatBenchmark(num_rows=num_rows)
    benchmark.run_benchmark()
    
    # Print results
    benchmark.print_comparison_table()
    
    # Save results
    benchmark.save_results_to_csv()
    
    logger.info("Benchmark completed successfully")


if __name__ == "__main__":
    main()
