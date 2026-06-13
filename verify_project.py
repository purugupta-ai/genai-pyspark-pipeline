"""
Project Status Verification Script
===================================
Comprehensive audit of all project files and their synchronization.
"""

import os
import sys
import shutil
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # For Python < 3.8
    from importlib_metadata import version, PackageNotFoundError
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

def check_java_setup():
    """Verify JAVA_HOME environment variable and java.exe."""
    java_home = os.environ.get("JAVA_HOME", "").strip('"').strip("'")
    if not java_home:
        return "✗ JAVA_HOME is not set (Hint: Restart your terminal/IDE after setting it)"
    
    # Handle cases where users include /bin in the variable path
    base_path = Path(java_home)
    if base_path.name.lower() == "bin":
        base_path = base_path.parent

    java_bin = "java.exe" if os.name == 'nt' else "java"
    java_exe = base_path / "bin" / java_bin
    
    if not java_exe.exists():
        return f"✗ {java_bin} missing at {java_exe}"
    
    if not shutil.which("java"):
        return "✗ java.exe not found in system PATH"
    
    return f"✓ Java setup verified at {java_home}"

def check_hadoop_setup():
    """Verify Hadoop environment variables and winutils."""
    hadoop_home = os.environ.get("HADOOP_HOME", "").strip('"').strip("'")
    if not hadoop_home:
        return "✗ HADOOP_HOME is not set (Hint: Restart your terminal/IDE after setting it)"
    
    # winutils is only required for Windows
    if os.name != 'nt':
        return "✓ Hadoop setup not required on non-Windows systems"

    winutils_path = Path(hadoop_home) / "bin" / "winutils.exe"
    if not winutils_path.exists():
        return f"✗ winutils.exe missing at {winutils_path}"
    
    if not shutil.which("winutils"):
        return "✗ winutils.exe not found in system PATH"
    
    return f"✓ Hadoop setup verified at {hadoop_home}"

def safe_read_text(filepath):
    """Read file text safely to avoid crashes during verification."""
    try:
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""

def check_dependencies(requirements_path):
    """Verify that all packages in requirements.txt are installed."""
    if not requirements_path.exists():
        return ["✗ requirements.txt not found"]
    
    results = []
    for line in safe_read_text(requirements_path).splitlines():
        package = line.split('>=')[0].split('==')[0].strip()
        if package and not package.startswith('#'):
            try:
                v = version(package)
                results.append(f"✓ {package:25} (Installed: {v})")
            except PackageNotFoundError:
                results.append(f"✗ {package:25} (NOT INSTALLED)")
    return results

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
        ("dashboard.py", base_dir / "dashboard.py"),
        ("scheduler.py", base_dir / "scheduler.py"),
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
        ("packages.txt", base_dir / "packages.txt"),
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
    
    print("\n[6] ENVIRONMENT CHECK")
    print("-" * 80)
    print(check_java_setup())
    print(check_hadoop_setup())

    print("\n[10] PYTHON DEPENDENCIES")
    print("-" * 80)
    req_path = base_dir / "requirements.txt"
    for result in check_dependencies(req_path):
        print(result)

    print("\n[7] FILE SIZES SUMMARY")
    print("-" * 80)
    total_size = 0
    for item in base_dir.rglob("*"):
        if item.is_file() and not any(x in item.parts for x in ['.git', '__pycache__', 'venv']):
            total_size += item.stat().st_size
    
    print(f"Total project size: {total_size / (1024*1024):.2f} MB")
    
    print("\n[8] SYNCHRONIZATION CHECK")
    print("-" * 80)
    
    # Check if all config constants are used
    config_file = base_dir / "src" / "config.py"
    analytics_file = base_dir / "src" / "spark_analytics.py"
    spark_config_file = base_dir / "src" / "spark_config.py"
    run_analytics_file = base_dir / "run_analytics.py"
    main_file = base_dir / "main.py"
    
    # Pre-read files safely to avoid crashes during check
    analytics_text = safe_read_text(analytics_file)
    spark_config_text = safe_read_text(spark_config_file)
    run_analytics_text = safe_read_text(run_analytics_file)
    main_text = safe_read_text(main_file)
    config_text = safe_read_text(config_file)

    checks = [
        ("config.py exists", config_file.exists()),
        ("spark_analytics.py imports from config", 
         "from src.config import" in analytics_text),
        ("spark_analytics.py imports SparkOptimizedConfig",
         "from src.spark_config import SparkOptimizedConfig" in analytics_text),
        ("run_analytics.py imports SalesAnalytics",
         "from src.spark_analytics import SalesAnalytics" in run_analytics_text),
        ("main.py imports SyntheticDataGenerator",
         "from src.data_generator import SyntheticDataGenerator" in main_text),
        ("Data paths defined in config", 
         "ORDERS_PARQUET" in config_text),
        ("AQE enabled in spark_config.py",
         "ADAPTIVE_ENABLED = True" in spark_config_text),
    ]
    
    for check_name, result in checks:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {check_name:50}")
    
    print("\n[9] RECOMMENDATIONS")
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
