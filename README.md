# ChurnBuster 360

## 1. 🚀 Project Title & Overview
**Project Name**: ChurnBuster 360: MLOps Pipeline for Customer Retention

**Goal**: To build a production-grade, end-to-end Machine Learning pipeline that identifies high-risk customers, automatically initiates a retention campaign, and provides a real-time dashboard for business insights.

**Key Technical Achievement**: Orchestrating a multi-stage data science workflow across a containerized environment (Docker/Airflow), featuring robust model versioning and PySpark data processing.

## 2. 💻 Solution Architecture (MLOps Pipeline)
The pipeline is managed by Apache Airflow and consists of 5 sequential, refactored tasks, ensuring data lineage and reliable execution.

| Stage | Tool/Operator | Function |
| ----- | ------------- | -------- |
| Ingestion | PythonOperator | Generates synthetic customer and transaction data (customers.csv, transactions.csv).|
| Processing | BashOperator (PySpark) | Runs a PySpark job to calculate RFM (Recency, Frequency, Monetary) features: days_since_last_txn, total_txns, and avg_txn_amount. |
| Training | PythonOperator | Trains a Random Forest Classifier and saves the model with a unique, date-versioned filename (churn_model_YYYYMMDD_HHMMSS.pkl).|
| Inference | PythonOperator | Loads the latest model version, generates churn probability scores for all customers, and saves the predictions.|
| Action | BashOperator (`send_alerts.py`) | Filters customers with P(Churn)>0.8 and simulates sending a retention email/discount (COMEBACK20 coupon), logging every action to `email_campaign_log.csv`.|

## 3. ✨ Key Technical Highlights
- Deployment Readiness: Successfully refactored core application logic (generate_data, train_model, predict_churn) from brittle BashOperator commands into the portable and safer PythonOperator.

- Model Versioning: Implemented a robust versioning system where models are saved with a timestamp, ensuring the prediction task always loads the correct and latest artifact.

- Containerization: The entire MLOps environment (Airflow Scheduler, Webserver, and Init services) is orchestrated using Docker Compose for local deployment fidelity. The backend database is SQLite (mounted as `airflow.db`), suitable for local/single-node execution.

- Data Processing at Scale: Utilized PySpark in the processing stage to handle large-scale feature engineering (RFM calculations).

## 4. 📊 Business Insights & Visualization
- A Streamlit Dashboard was deployed to provide a single source of truth for the business team:

### Core Findings (Feature Importance):

The Random Forest Model revealed that customer retention is driven primarily by Frequency and Recency:

1. Total Transactions (total_txns): The strongest predictor of churn. Customers with low overall engagement are most likely to leave, regardless of transaction recency.

2. Days Since Last Transaction (days_since_last_txn): The second strongest predictor.

3. Average Transaction Amount (avg_txn_amount): The weakest predictor, indicating that spending habits are less important than engagement habits.

### Actionable Retention Loop:

The pipeline is designed to be active:

1. The model predicts churn.

2. The pipeline sends a retention email (COMEBACK20 coupon) to all customers above the 80% risk threshold.

3. The Streamlit dashboard tracks the customer list and the real-time campaign logs, allowing Marketing to monitor the impact.

## 5. 🛠️ Setup and Execution

This project assumes you are running in a Linux-based environment (like a VS Code Codespace) with Docker installed.

### A. Clone and Build

1. Clone the repository:

        git clone <your_repo_url>
        cd ChurnBuster-360

2. Start the Airflow Stack (This will pull the image and create the containers):

        docker compose up -d

### B. Execute the Pipeline

1. Access the Airflow UI (typically http://localhost:8080).

2. Unpause the DAG named churnbuster_etl_local.

3. Click Trigger DAG.

### C. Launch the Dashboard

1. Install dependencies on your host machine/Codespace terminal:

        pip install -r requirements.txt

2. Run the application:

        streamlit run src/dashboard/app.py

3. Access the Streamlit URL (e.g., http://localhost:8501) to view the real-time predictions and campaign logs.

> **Note**: Run `streamlit run src/dashboard/app.py` from the **project root directory** to ensure relative data paths resolve correctly.

---

## 6. ⚠️ Known Limitations (Prototype)

This project is a portfolio prototype. The following are known simplifications relative to a production system:

- **Target Leakage**: The churn label in `train_model.py` is derived from `days_since_last_txn` (a training feature), which inflates model accuracy. In production, the `is_churn` label from the source data — or a ground-truth label from CRM records — would be used instead.
- **SQLite Backend**: Docker Compose uses SQLite for Airflow's metadata DB. Multi-container SQLite access can cause sync issues; production deployments should use PostgreSQL.
- **No Cloud Storage**: All pipeline artifacts are written to local Docker volumes. The `infra/` Terraform configs (now removed) were scaffolded for a future GCS/BigQuery integration.
- **Simulated Email Sending**: `send_alerts.py` logs emails to CSV instead of calling a real email API (e.g., SendGrid, AWS SES).
- **Runtime Dependency Install**: `train_model_python()` in the DAG installs packages at runtime via `pip`. This should be moved to the Docker image build step for production use.