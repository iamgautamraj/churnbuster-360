import pandas as pd
import joblib
import os
import argparse
import glob

def find_latest_model(model_dir):
    """Finds the path to the newest model version in the specified directory."""
    
    # Search for all files matching the version pattern: churn_model_YYYYMMDD_HHMMSS.pkl
    list_of_files = glob.glob(os.path.join(model_dir, 'churn_model_*.pkl'))
    
    if not list_of_files:
        raise FileNotFoundError(f"No model files found in {model_dir}")

    # Find the newest file by creation time (or name, as names are timestamped)
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def make_predictions(model_dir):
    print("🔮 Starting Inference...")

    # Paths
    features_path = "/opt/airflow/data/processed/churn_features.parquet"
    model_path = find_latest_model(model_dir)
    output_path = "/opt/airflow/data/processed/final_predictions.csv"

    # Extract version ID from filename for logging
    version_id = os.path.basename(model_path).replace('.pkl', '').replace('churn_model_', '')

    # 1. Load Data and Model
    print(f"📂 Loading data and model version: {version_id}...")
    if not os.path.exists(model_path):
        raise FileNotFoundError("❌ Model not found! Train the model first.")
    
    df = pd.read_parquet(features_path)
    model = joblib.load(model_path)

    # 2. Prepare Features
    # Must match the training features exactly
    feature_cols = ['total_txns', 'avg_txn_amount', 'days_since_last_txn']
    X = df[feature_cols]

    # 3. Predict
    print("🤖 Generating predictions...")
    # predict_proba returns [prob_0, prob_1]. We want prob_1 (churn probability)
    probabilities = model.predict_proba(X)[:, 1]
    predictions = model.predict(X)

    # 4. Attach predictions to the dataframe
    df['churn_prediction'] = predictions
    df['churn_probability'] = probabilities

    # 5. Filter for High Risk Customers (Prob > 70%)
    high_risk_customers = df[df['churn_probability'] > 0.7].sort_values(by='churn_probability', ascending=False)
    
    print(f"⚠️ Identified {len(high_risk_customers)} high-risk customers!")
    print(high_risk_customers[['customer_id', 'days_since_last_txn', 'churn_probability']].head())

    # 6. Save Results
    df.to_csv(output_path, index=False)
    print(f"✅ Predictions saved to {output_path}")

# --- UPDATED MAIN BLOCK TO HANDLE ARGS ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Define the argument expected from the BashOperator
    parser.add_argument('--model-dir', required=True, help='Directory containing the trained models')
    args = parser.parse_args()
    
    make_predictions(args.model_dir)