import os
import random
import argparse
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

# Initialize Faker
fake = Faker()

class DataGenerator:
    def __init__(self, output_dir="data/raw"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_customers(self, count=1000):
        print(f"Generating {count} customers...")
        customers = []
        for _ in range(count):
            cust_id = fake.uuid4()
            # 20% Churn Rate Simulation
            is_churn = 1 if random.random() < 0.2 else 0
            
            customers.append({
                "customer_id": cust_id,
                "name": fake.name(),
                "age": random.randint(18, 75),
                "city": fake.city(),
                "join_date": fake.date_between(start_date='-2y', end_date='-6m'),
                "is_churn": is_churn
            })
        
        df = pd.DataFrame(customers)
        path = f"{self.output_dir}/customers.csv"
        df.to_csv(path, index=False)
        print(f"✅ Saved customers to {path}")
        return df

    def generate_transactions(self, customers_df):
        print("Generating transaction history...")
        transactions = []
        
        # Explicitly define start date (6 months ago)
        start_date = datetime.now() - timedelta(days=180)
        
        for _, cust in customers_df.iterrows():
            cust_id = cust['customer_id']
            is_churn = cust['is_churn']
            
            # Logic: Churned users stop transacting 30 days ago
            if is_churn:
                num_txns = random.randint(0, 5) 
                end_date_limit = datetime.now() - timedelta(days=30)
            else:
                num_txns = random.randint(20, 100)
                end_date_limit = datetime.now()
            
            for _ in range(num_txns):
                # FIX: Use date_time_between and ensure strict types
                txn_date = fake.date_time_between(start_date=start_date, end_date=end_date_limit)
                
                transactions.append({
                    "txn_id": fake.uuid4(),
                    "customer_id": cust_id,
                    "amount": round(random.uniform(10.0, 5000.0), 2),
                    "txn_date": txn_date,
                    "category": random.choice(['Groceries', 'Tech', 'Travel', 'Utilities']),
                    "payment_method": random.choice(['Credit Card', 'UPI', 'Debit Card'])
                })

        df = pd.DataFrame(transactions)
        path = f"{self.output_dir}/transactions.csv"
        df.to_csv(path, index=False)
        print(f"✅ Saved {len(df)} transactions to {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Dummy Banking Data")
    parser.add_argument("--count", type=int, default=1000, help="Number of customers")
    args = parser.parse_args()

    gen = DataGenerator()
    df_cust = gen.generate_customers(count=args.count)
    gen.generate_transactions(df_cust)