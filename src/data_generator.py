import csv
import random
from faker import Faker
from typing import List, Dict, Any
from src.config import setup_logging, CUSTOMERS_FILE, PRODUCTS_FILE, ORDERS_FILE, RAW_DATA_DIR

logger = setup_logging(__name__)
fake = Faker()

def ensure_dirs_exist() -> None:
    """Creates the necessary data directories if they do not exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {RAW_DATA_DIR}")

def generate_customers(num_records: int = 100) -> List[Dict[str, Any]]:
    """
    Generates a list of fake customer dictionaries.

    Args:
        num_records (int): Number of customer records to generate.

    Returns:
        List[Dict[str, Any]]: A list containing customer data dictionaries.
    """
    logger.info(f"Generating {num_records} customers...")
    customers = []
    for i in range(1, num_records + 1):
        customers.append({
            "customer_id": i,
            "name": fake.name(),
            "email": fake.email(),
            "country": fake.country()
        })
    return customers

def generate_products(num_records: int = 20) -> List[Dict[str, Any]]:
    """
    Generates a list of fake product dictionaries.

    Args:
        num_records (int): Number of product records to generate.

    Returns:
        List[Dict[str, Any]]: A list containing product data dictionaries.
    """
    logger.info(f"Generating {num_records} products...")
    products = []
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Toys']
    for i in range(1, num_records + 1):
        products.append({
            "product_id": i,
            "product_name": fake.word().capitalize(),
            "category": random.choice(categories),
            "price": round(random.uniform(10.0, 500.0), 2)
        })
    return products

def generate_orders(num_records: int = 500, num_customers: int = 100, num_products: int = 20) -> List[Dict[str, Any]]:
    """
    Generates a list of fake order dictionaries linked to customers and products.

    Args:
        num_records (int): Number of order records to generate.
        num_customers (int): Max customer ID to reference.
        num_products (int): Max product ID to reference.

    Returns:
        List[Dict[str, Any]]: A list containing order data dictionaries.
    """
    logger.info(f"Generating {num_records} orders...")
    orders = []
    for i in range(1, num_records + 1):
        orders.append({
            "order_id": i,
            "customer_id": random.randint(1, num_customers),
            "product_id": random.randint(1, num_products),
            "quantity": random.randint(1, 5),
            "order_date": fake.date_between(start_date='-1y', end_date='today').isoformat()
        })
    return orders

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Saves a list of dictionaries to a CSV file.

    Args:
        data (List[Dict[str, Any]]): Data to save.
        filepath (str): Full path to the output CSV file.
    """
    if not data:
        logger.warning(f"No data to save for {filepath}")
        return

    keys = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    logger.info(f"Successfully saved data to {filepath}")

def main() -> None:
    """Main execution function to run the data generation pipeline."""
    logger.info("Starting Data Generation Process")
    ensure_dirs_exist()
    
    num_customers = 100
    num_products = 50
    num_orders = 1000

    customers = generate_customers(num_customers)
    products = generate_products(num_products)
    orders = generate_orders(num_orders, num_customers, num_products)

    save_to_csv(customers, CUSTOMERS_FILE)
    save_to_csv(products, PRODUCTS_FILE)
    save_to_csv(orders, ORDERS_FILE)
    
    logger.info("Data Generation Process Complete")

if __name__ == "__main__":
    main()