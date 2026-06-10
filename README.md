# E-Commerce Data Pipeline: PySpark Analytics

## Project Purpose
This project simulates an e-commerce data pipeline. It generates realistic fake data (customers, products, and orders) and uses PySpark to process and analyze that data to extract business insights.

## Project Structure
- `src/`: Source code for data generation and PySpark analytics.
- `data/raw/`: Generated CSV files simulating database extracts.
- `data/processed/`: The output of our PySpark aggregations.
- `notebooks/`: For exploratory data analysis (EDA).
- `tests/`: Unit test scripts.

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Generate raw data: `python src/data_generator.py`
3. Run PySpark analytics: `python src/spark_analytics.py`