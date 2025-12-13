from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_date, datediff, count, avg, max as max_, when, lit
import os

def process_data():
    # 1. Initialize Spark Session (Local Mode)
    # We set 'spark.driver.memory' to ensure it doesn't crash your Codespace
    spark = SparkSession.builder \
        .appName("ChurnFeatureEngineering") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

    print("🚀 Spark Session Started...")

    # 2. Read Raw Data
    # inferSchema=True tells Spark to guess if '12.50' is a float or string
    df_cust = spark.read.csv("data/raw/customers.csv", header=True, inferSchema=True)
    df_txns = spark.read.csv("data/raw/transactions.csv", header=True, inferSchema=True)
    

    print(f"📊 Raw Data Loaded. Customers: {df_cust.count()}, Transactions: {df_txns.count()}")

    # 3. Feature Engineering: Aggregate Transactions at Customer Level
    # Logic: We want one row per customer with their behavioral stats
    cust_features = df_txns.groupBy("customer_id").agg(
        count("txn_id").alias("total_txns"),
        avg("amount").alias("avg_txn_amount"),
        max_("txn_date").alias("last_txn_date")
    )

    # 4. Join with Customer Profile
    # "left" join ensures we keep customers even if they have 0 transactions
    final_df = df_cust.join(cust_features, on="customer_id", how="left")

    # 5. Advanced Feature: 'Days Since Last Transaction' (Recency)
    # Handle NULLs: If they never transacted, assume 365 days (inactive)
    final_df = final_df.withColumn(
        "days_since_last_txn",
        datediff(current_date(), col("last_txn_date"))
    ).fillna(365, subset=["days_since_last_txn"]) \
     .fillna(0, subset=["total_txns", "avg_txn_amount"])

    # 6. Show a sneak peek
    print("👀 Preview of Feature Store:")
    final_df.select("customer_id", "age", "total_txns", "avg_txn_amount", "days_since_last_txn", "is_churn").show(5)

    # 7. Write to Parquet (The "Silver" Layer)
    # Parquet is compressed and much faster than CSV
    output_path = "data/processed/churn_features"
    final_df.write.mode("overwrite").parquet(output_path)
    print(f"✅ Data processed and saved to {output_path}")

    spark.stop()

if __name__ == "__main__":
    process_data()