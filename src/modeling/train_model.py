import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from datetime import datetime

def train_model():
    print("🧠 Starting Model Training...")

    # Define Paths
    # Note: We use the Docker path /opt/airflow/...
    input_path = "/opt/airflow/data/processed/churn_features.parquet"
    version_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = f"/opt/airflow/data/model/churn_model_{version_id}.pkl"

    # Ensure model directory exists
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    # 1. Load Data
    print(f"📂 Loading data from {input_path}...")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    print(f"✅ Data Loaded. Shape: {df.shape}")

    # 2. Prepare Features (X) and Target (y)
    # We need a target variable. Since our synthetic data generator didn't explicitly 
    # create a 'churn' label yet, let's create a dummy rule for this prototype:
    # Rule: If days_since_last_txn > 30, they have churned (1), else (0)
    
    print("🛠️ Creating target variable (Simulated for prototype)...")
    df['churn'] = df['days_since_last_txn'].apply(lambda x: 1 if x > 30 else 0)

    features = ['total_txns', 'avg_txn_amount', 'days_since_last_txn']
    X = df[features]
    y = df['churn']

    # 3. Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Model
    print("🤖 Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"📊 Model Accuracy: {accuracy:.2f}")
    print("📝 Classification Report:")
    print(classification_report(y_test, predictions))

# ... (after evaluation and before saving the model)

    # 5. Evaluate
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"📊 Model Accuracy: {accuracy:.2f}")
    print("📝 Classification Report:")
    print(classification_report(y_test, predictions))

    # --- NEW: SAVE FEATURE IMPORTANCE ---
    print("💾 Saving Feature Importances...")
    importances = pd.DataFrame({
        'feature': features,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    importance_path = "/opt/airflow/data/model/feature_importances.csv"
    importances.to_csv(importance_path, index=False)

    # 6. Save Model
    joblib.dump(model, model_path)
    # --- UPDATED PRINT STATEMENT ---
    print(f"💾 Model version {version_id} saved to {model_path}")
    print(f"--- MODEL METADATA ---")
    print(f"VERSION: {version_id}")
    print(f"ACCURACY: {accuracy}")
    print(f"----------------------")

if __name__ == "__main__":
    train_model()