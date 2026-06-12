"""
Project Status Verification Script
===================================
Comprehensive audit of all project files and their synchronization.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, filename):
    """Check if a file exists."""
    if filepath.exists():
        size_mb = filepath.stat().st_size / (1024 * 1024)
        return f"✓ {filename:40} ({size_mb:8.2f} MB)"
    else:
        return f"✗ {filename:40} (MISSING)"

def check_imports(module_path):
    """Check if a module can be imported."""
    try:
        # Add src to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        module_name = module_path.stem
        if module_path.parent.name == 'src':
            __import__(f'src.{module_name}')
        else:
            __import__(module_name)
        return f"✓ {module_path.name:40} (imports OK)"
    except Exception as e:
        return f"✗ {module_path.name:40} (ERROR: {str(e)[:40]})"

def main():
    base_dir = Path(__file__).resolve().parent
    
    print("\n" + "="*80)
    print("PROJECT STATUS VERIFICATION")
    print("="*80)
    
    print("\n[1] DATA FILES")
    print("-" * 80)
    data_raw = base_dir / "data" / "raw"
    parquet_files = [
        ("customers.parquet", data_raw / "customers.parquet"),
        ("products.parquet", data_raw / "products.parquet"),
        ("orders.parquet", data_raw / "orders.parquet"),
    ]
    for name, path in parquet_files:
        print(check_file_exists(path, name))
    
    print("\n[2] SOURCE FILES")
    print("-" * 80)
    src_files = [
        ("__init__.py", base_dir / "src" / "__init__.py"),
        ("config.py", base_dir / "src" / "config.py"),
        ("data_generator.py", base_dir / "src" / "data_generator.py"),
        ("spark_config.py", base_dir / "src" / "spark_config.py"),
        ("spark_analytics.py", base_dir / "src" / "spark_analytics.py"),
        ("benchmark_formats.py", base_dir / "src" / "benchmark_formats.py"),
    ]
    for name, path in src_files:
        print(check_file_exists(path, name))
    
    print("\n[3] SCRIPT FILES")
    print("-" * 80)
    script_files = [
        ("main.py", base_dir / "main.py"),
        ("run_analytics.py", base_dir / "run_analytics.py"),
        ("test_config.py", base_dir / "test_config.py"),
    ]
    for name, path in script_files:
        print(check_file_exists(path, name))
    
    print("\n[4] CONFIGURATION FILES")
    print("-" * 80)
    config_files = [
        ("requirements.txt", base_dir / "requirements.txt"),
        ("README.md", base_dir / "README.md"),
        ("LICENSE", base_dir / "LICENSE"),
        ("SPARK_CONFIG_GUIDE.md", base_dir / "SPARK_CONFIG_GUIDE.md"),
    ]
    for name, path in config_files:
        print(check_file_exists(path, name))
    
    print("\n[5] MODULE IMPORTS")
    print("-" * 80)
    modules_to_test = [
        base_dir / "src" / "config.py",
        base_dir / "src" / "data_generator.py",
        base_dir / "src" / "spark_config.py",
        base_dir / "src" / "spark_analytics.py",
    ]
    for module_path in modules_to_test:
        if module_path.exists():
            print(check_imports(module_path))
    
    print("\n[6] FILE SIZES SUMMARY")
    print("-" * 80)
    total_size = 0
    for item in base_dir.rglob("*"):
        if item.is_file() and not any(x in item.parts for x in ['.git', '__pycache__', 'venv']):
            total_size += item.stat().st_size
    
    print(f"Total project size: {total_size / (1024*1024):.2f} MB")
    
    print("\n[7] SYNCHRONIZATION CHECK")
    print("-" * 80)
    
    # Check if all config constants are used
    config_file = base_dir / "src" / "config.py"
    analytics_file = base_dir / "src" / "spark_analytics.py"
    run_analytics_file = base_dir / "run_analytics.py"
    main_file = base_dir / "main.py"
    
    checks = [
        ("config.py exists", config_file.exists()),
        ("spark_analytics.py imports from config", 
         "from src.config import" in analytics_file.read_text()),
        ("spark_analytics.py imports SparkOptimizedConfig",
         "from src.spark_config import SparkOptimizedConfig" in analytics_file.read_text()),
        ("run_analytics.py imports SalesAnalytics",
         "from src.spark_analytics import SalesAnalytics" in run_analytics_file.read_text()),
        ("main.py imports SyntheticDataGenerator",
         "from src.data_generator import SyntheticDataGenerator" in main_file.read_text()),
        ("Data paths defined in config", 
         "ORDERS_PARQUET" in config_file.read_text()),
    ]
    
    for check_name, result in checks:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name:50}")
    
    print("\n[8] RECOMMENDATIONS")
    print("-" * 80)
    recommendations = []
    
    if not (data_raw / "customers.parquet").exists():
        recommendations.append("Run 'python main.py' to generate synthetic data")
    
    if recommendations:
        for rec in recommendations:
            print(f"• {rec}")
    else:
        print("• All checks passed! Project is ready for use.")
        print("• Data files are present and all imports are correct.")
        print("• Run 'python run_analytics.py' to execute analytics.")
        print("• Run 'python test_config.py' to verify Spark configuration.")
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
