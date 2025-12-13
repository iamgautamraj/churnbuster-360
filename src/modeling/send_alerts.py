import pandas as pd
import os
from datetime import datetime

def send_retention_emails():
    print("📧 Starting Retention Campaign...")

    # Paths
    input_path = "/opt/airflow/data/processed/final_predictions.csv"
    log_path = "/opt/airflow/data/processed/email_campaign_log.csv"

    # 1. Load Predictions
    if not os.path.exists(input_path):
        print("❌ Predictions file not found.")
        return
    
    df = pd.read_csv(input_path)

    # 2. Filter for "Urgent" Churn Risk (Probability > 0.8)
    # We only want to spend money (discounts) on people who are really leaving.
    target_customers = df[df['churn_probability'] > 0.8].copy()

    if target_customers.empty:
        print("✅ No high-risk customers found today. No emails sent.")
        return

    print(f"⚠️ Found {len(target_customers)} customers at high risk.")

    # 3. Simulate Sending Emails
    # In a real job, you would use smtplib or an API like SendGrid here.
    # For this project, we will log the "sent" emails.
    
    email_log = []
    
    for index, row in target_customers.iterrows():
        # Personalize the message
        customer_name = row['name']
        customer_email = f"{row['customer_id'][:8]}@example.com" # Mock email
        discount_code = "COMEBACK20"
        
        # The Logic:
        message = (
            f"Sending Email to: {customer_name} <{customer_email}>\n"
            f"Subject: We miss you! Here is 20% OFF.\n"
            f"Body: Hey {customer_name}, it's been {row['days_since_last_txn']} days since we saw you. "
            f"Use code {discount_code} for your next purchase!\n"
            "---------------------------------------------------"
        )
        print(message)
        
        # Log it
        email_log.append({
            "customer_id": row['customer_id'],
            "name": row['name'],
            "sent_at": datetime.now(),
            "campaign": "Churn_Retention_20_Percent",
            "status": "Sent"
        })

    # 4. Save the Log
    # This serves as our "Audit Trail" for the dashboard later
    log_df = pd.DataFrame(email_log)
    
    # Append to existing log if it exists, else create new
    if os.path.exists(log_path):
        log_df.to_csv(log_path, mode='a', header=False, index=False)
    else:
        log_df.to_csv(log_path, mode='w', header=True, index=False)
        
    print(f"✅ Campaign Complete. {len(log_df)} emails logged to {log_path}")

if __name__ == "__main__":
    send_retention_emails()