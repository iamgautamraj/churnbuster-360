from pyspark.sql import SparkSession
# Consolidate all imports at the top
from pyspark.sql.functions import col, lit, when, datediff, current_date, count, max, avg, to_date

def process_data():
    # Initialize Spark Session
    spark = SparkSession.builder \
        .appName("ChurnFeatureEng") \
        .getOrCreate()

    print("🚀 Spark Session Started...")

    # Load Data (USING ABSOLUTE PATHS)
    customers_path = "/opt/airflow/data/raw/customers.csv"
    transactions_path = "/opt/airflow/data/raw/transactions.csv"
    output_path = "/opt/airflow/data/processed/churn_features.parquet"

    df_cust = spark.read.csv(customers_path, header=True, inferSchema=True)
    df_txns = spark.read.csv(transactions_path, header=True, inferSchema=True)

    print(f"📊 Raw Data Loaded. Customers: {df_cust.count()}, Transactions: {df_txns.count()}")

    # --- Feature Engineering ---
    
    # Convert string dates to actual dates
    df_txns = df_txns.withColumn("txn_date", to_date(col("txn_date")))
    
    # Get reference date (today)
    ref_date = current_date()

    # Calculate Aggregates (Recency, Frequency, Monetary)
    # This replaces all the previous broken/duplicate logic
    cust_stats = df_txns.groupBy("customer_id").agg(
        count("txn_id").alias("total_txns"),
        avg("amount").alias("avg_txn_amount"),
        datediff(ref_date, max("txn_date")).alias("days_since_last_txn")
    )

    # Join with Customer Profile
    final_df = df_cust.join(cust_stats, on="customer_id", how="left")
    
    # Fill NA for customers with no transactions
    final_df = final_df.na.fill({
        "total_txns": 0,
        "avg_txn_amount": 0.0,
        "days_since_last_txn": 999
    })

    print("👀 Preview of Feature Store:")
    final_df.show(5)

    # Save to Parquet (Feature Store)
    final_df.write.mode("overwrite").parquet(output_path)
    print(f"✅ Data processed and saved to {output_path}")

    spark.stop()

if __name__ == "__main__":
    process_data()