"""
Synthetic Data Generator for E-Commerce Pipeline.

This module provides a SyntheticDataGenerator class that creates realistic e-commerce
datasets including customers, products, and orders with realistic statistical distributions.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd
from faker import Faker
from tqdm import tqdm

from src.config import setup_logging, CUSTOMERS_FILE, PRODUCTS_FILE, ORDERS_FILE, RAW_DATA_DIR

logger = setup_logging(__name__)


class SyntheticDataGenerator:
    """
    Generate realistic synthetic e-commerce data for customers, products, and orders.
    
    This class uses statistical distributions to create realistic data:
    - Faker for generating realistic names and emails
    - NumPy normal distribution for customer ages (mean=35)
    - NumPy Pareto distribution for order quantity (80/20 rule)
    - tqdm for progress tracking during generation
    
    Attributes:
        num_customers (int): Number of customers to generate
        num_products (int): Number of products to generate
        num_orders (int): Number of orders to generate
        random_seed (int): Random seed for reproducibility
    """
    
    # Product categories
    CATEGORIES = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    
    # Price range for products
    MIN_PRICE = 10.0
    MAX_PRICE = 500.0
    
    # Customer age parameters
    AGE_MEAN = 35
    AGE_STD = 12
    AGE_MIN = 18
    AGE_MAX = 80
    
    # Product stock range
    MIN_STOCK = 5
    MAX_STOCK = 1000
    
    # Order quantity parameters (Pareto distributed)
    PARETO_SHAPE = 1.5  # Controls 80/20 distribution
    MIN_QUANTITY = 1
    MAX_QUANTITY = 10
    
    def __init__(
        self,
        num_customers: int = 100_000,
        num_products: int = 10_000,
        num_orders: int = 1_000_000,
        random_seed: int = 42,
    ):
        """
        Initialize the SyntheticDataGenerator.
        
        Args:
            num_customers (int): Number of customers to generate. Default: 100,000
            num_products (int): Number of products to generate. Default: 10,000
            num_orders (int): Number of orders to generate. Default: 1,000,000
            random_seed (int): Random seed for reproducibility. Default: 42
        """
        self.num_customers = num_customers
        self.num_products = num_products
        self.num_orders = num_orders
        self.random_seed = random_seed
        
        # Set seeds for reproducibility
        np.random.seed(random_seed)
        
        self.faker = Faker()
        Faker.seed(random_seed)
        
        logger.info(
            f"Initialized SyntheticDataGenerator with: "
            f"{num_customers:,} customers, {num_products:,} products, {num_orders:,} orders"
        )
    
    def generate_customers(self) -> pd.DataFrame:
        """
        Generate a DataFrame of customers with realistic attributes.
        
        Generates:
        - customer_id: Unique customer identifier
        - name: Faker-generated customer name
        - email: Faker-generated email address
        - age: Normal distribution (mean=35, std=12, range=[18, 80])
        - city: Faker-generated city
        - country: Faker-generated country
        - registration_date: Random date within last 3 years
        
        Returns:
            pd.DataFrame: Customer data with columns:
                [customer_id, name, email, age, city, country, registration_date]
        """
        logger.info(f"Generating {self.num_customers:,} customers...")
        
        customers = {
            "customer_id": [],
            "name": [],
            "email": [],
            "age": [],
            "city": [],
            "country": [],
            "registration_date": [],
        }
        
        # Generate ages using normal distribution
        ages = np.random.normal(
            self.AGE_MEAN, self.AGE_STD, self.num_customers
        ).astype(int)
        ages = np.clip(ages, self.AGE_MIN, self.AGE_MAX)
        
        # Generate registration dates (within last 3 years)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 3)
        date_range = (end_date - start_date).days
        
        for i in tqdm(range(1, self.num_customers + 1), desc="Customers"):
            customers["customer_id"].append(i)
            customers["name"].append(self.faker.name())
            customers["email"].append(self.faker.email())
            customers["age"].append(ages[i - 1])
            customers["city"].append(self.faker.city())
            customers["country"].append(self.faker.country())
            
            # Random registration date
            random_days = np.random.randint(0, date_range)
            reg_date = start_date + timedelta(days=int(random_days))
            customers["registration_date"].append(reg_date.date())
        
        df = pd.DataFrame(customers)
        logger.info(f"Generated {len(df):,} customers with shape {df.shape}")
        return df
    
    def generate_products(self) -> pd.DataFrame:
        """
        Generate a DataFrame of products with realistic attributes.
        
        Generates:
        - product_id: Unique product identifier
        - name: Faker-generated product name
        - category: Random selection from [Electronics, Clothing, Home, Sports, Books]
        - price: Uniform distribution [10, 500]
        - stock: Uniform distribution [5, 1000]
        - rating: Uniform distribution [1, 5]
        
        Returns:
            pd.DataFrame: Product data with columns:
                [product_id, name, category, price, stock, rating]
        """
        logger.info(f"Generating {self.num_products:,} products...")
        
        products = {
            "product_id": [],
            "name": [],
            "category": [],
            "price": [],
            "stock": [],
            "rating": [],
        }
        
        for i in tqdm(range(1, self.num_products + 1), desc="Products"):
            products["product_id"].append(i)
            products["name"].append(self.faker.word().capitalize())
            products["category"].append(np.random.choice(self.CATEGORIES))
            products["price"].append(
                round(
                    np.random.uniform(self.MIN_PRICE, self.MAX_PRICE), 2
                )
            )
            products["stock"].append(
                np.random.randint(self.MIN_STOCK, self.MAX_STOCK + 1)
            )
            # Rating with slight skew towards higher ratings
            products["rating"].append(
                round(np.random.uniform(1.0, 5.0), 1)
            )
        
        df = pd.DataFrame(products)
        logger.info(f"Generated {len(df):,} products with shape {df.shape}")
        return df
    
    def generate_orders(self) -> pd.DataFrame:
        """
        Generate a DataFrame of orders with realistic distribution.
        
        Uses Pareto distribution to implement the 80/20 rule:
        - 20% of customers generate 80% of orders
        
        Generates:
        - order_id: Unique order identifier
        - customer_id: Reference to customer
        - product_id: Reference to product
        - quantity: Pareto-distributed [1, 10]
        - order_date: Random date within last 2 years
        
        Returns:
            pd.DataFrame: Order data with columns:
                [order_id, customer_id, product_id, quantity, order_date]
        """
        logger.info(f"Generating {self.num_orders:,} orders (Pareto distribution)...")
        
        orders = {
            "order_id": [],
            "customer_id": [],
            "product_id": [],
            "quantity": [],
            "order_date": [],
        }
        
        # Generate orders with Pareto distribution for customers
        # This ensures 20% of customers make 80% of orders
        customer_ids = np.random.pareto(
            self.PARETO_SHAPE, self.num_orders
        )
        customer_ids = (customer_ids * (self.num_customers - 1) + 1).astype(int)
        customer_ids = np.clip(customer_ids, 1, self.num_customers)
        
        # Generate order dates (within last 2 years)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 2)
        date_range = (end_date - start_date).days
        
        # Generate quantities using Pareto distribution
        quantities = np.random.pareto(
            self.PARETO_SHAPE, self.num_orders
        )
        quantities = (quantities + 1).astype(int)
        quantities = np.clip(quantities, self.MIN_QUANTITY, self.MAX_QUANTITY)
        
        for i in tqdm(range(1, self.num_orders + 1), desc="Orders"):
            orders["order_id"].append(i)
            orders["customer_id"].append(customer_ids[i - 1])
            orders["product_id"].append(
                np.random.randint(1, self.num_products + 1)
            )
            orders["quantity"].append(quantities[i - 1])
            
            # Random order date
            random_days = np.random.randint(0, date_range)
            order_date = start_date + timedelta(days=int(random_days))
            orders["order_date"].append(order_date.date())
        
        df = pd.DataFrame(orders)
        logger.info(f"Generated {len(df):,} orders with shape {df.shape}")
        return df
    
    def generate_all(
        self,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generate all datasets (customers, products, orders).
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
                (customers_df, products_df, orders_df)
        """
        logger.info("Starting complete synthetic data generation...")
        
        customers_df = self.generate_customers()
        products_df = self.generate_products()
        orders_df = self.generate_orders()
        
        logger.info("Completed synthetic data generation for all datasets")
        return customers_df, products_df, orders_df
    
    def save_to_csv(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        orders_df: pd.DataFrame,
    ) -> None:
        """
        Save all DataFrames to CSV files.
        
        Args:
            customers_df (pd.DataFrame): Customers data
            products_df (pd.DataFrame): Products data
            orders_df (pd.DataFrame): Orders data
        """
        logger.info("Saving generated data to CSV files...")
        
        # Ensure directory exists
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        customers_df.to_csv(CUSTOMERS_FILE, index=False)
        logger.info(f"Saved {len(customers_df):,} customers to {CUSTOMERS_FILE}")
        
        products_df.to_csv(PRODUCTS_FILE, index=False)
        logger.info(f"Saved {len(products_df):,} products to {PRODUCTS_FILE}")
        
        orders_df.to_csv(ORDERS_FILE, index=False)
        logger.info(f"Saved {len(orders_df):,} orders to {ORDERS_FILE}")


def main() -> None:
    """Main execution function to run the data generation pipeline."""
    logger.info("Starting E-Commerce Synthetic Data Generation Pipeline")
    
    # Initialize generator with default parameters
    generator = SyntheticDataGenerator(
        num_customers=100_000,
        num_products=10_000,
        num_orders=1_000_000,
    )
    
    # Generate all datasets
    customers_df, products_df, orders_df = generator.generate_all()
    
    # Save to CSV
    generator.save_to_csv(customers_df, products_df, orders_df)
    
    logger.info("E-Commerce Data Generation Pipeline Complete")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("SYNTHETIC DATA GENERATION SUMMARY")
    print("=" * 60)
    print(f"Customers: {len(customers_df):,}")
    print(f"  - Age range: {customers_df['age'].min()} - {customers_df['age'].max()}")
    print(f"  - Date range: {customers_df['registration_date'].min()} to {customers_df['registration_date'].max()}")
    print(f"\nProducts: {len(products_df):,}")
    print(f"  - Price range: ${products_df['price'].min():.2f} - ${products_df['price'].max():.2f}")
    print(f"  - Rating range: {products_df['rating'].min():.1f} - {products_df['rating'].max():.1f}")
    print(f"  - Stock range: {products_df['stock'].min()} - {products_df['stock'].max()}")
    print(f"\nOrders: {len(orders_df):,}")
    print(f"  - Date range: {orders_df['order_date'].min()} to {orders_df['order_date'].max()}")
    print(f"  - Quantity range: {orders_df['quantity'].min()} - {orders_df['quantity'].max()}")
    print(f"  - Top 20% customers: {int(len(customers_df) * 0.2):,} (Pareto 80/20 rule)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()