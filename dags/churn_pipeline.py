from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator

# --- NEW IMPORTS ---
import os
import sys

sys.path.append(os.path.join(os.environ['AIRFLOW_HOME'], 'src', 'ingestion'))
# Add source directories to Python path
AIRFLOW_SRC = os.path.join(os.environ['AIRFLOW_HOME'], 'src')
sys.path.append(os.path.join(AIRFLOW_SRC, 'ingestion')) 
sys.path.append(os.path.join(AIRFLOW_SRC, 'modeling')) # ADDED MODELING PATH

# Now import the class from the file you provided
from generate_data import DataGenerator 
# --- END NEW IMPORTS ---
# --- NEW IMPORTS ---
from train_model import train_model as train_model_func
from predict import make_predictions as predict_churn_func
# --- END NEW IMPORTS ---

default_args = {
    'owner': 'churnbuster',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def generate_synthetic_data_python(count=1000):
    # The output directory in the generator class should match the Docker mount
    # Since your original script uses "data/raw", we'll match that.
    
    # Instantiate the generator, specifying the Airflow-accessible path
    # NOTE: The default output_dir is "data/raw" in your script. We need to 
    # ensure it aligns with the absolute path inside the container.
    generator = DataGenerator(output_dir="/opt/airflow/data/raw") 
    
    # Execute the core logic
    df_cust = generator.generate_customers(count=count)
    generator.generate_transactions(df_cust)

    print(f"✅ Data generation complete for {count} customers.")

def train_model_python():
    # Since this task runs in its own environment, we must ensure the core ML library is present.
    # While we are trying to avoid pip in the bash operator, installing key dependencies 
    # within the PythonOperator is often necessary if the Airflow environment isn't fully pre-built.
    import subprocess
    import sys
    
    # Ensure Scikit-learn and pandas are installed
    subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn", "pandas", "pyarrow"])
    
    # Call the imported function
    train_model_func()

def predict_churn_python():
    # Pass the required directory argument to the imported function
    model_dir = "/opt/airflow/data/model/"
    predict_churn_func(model_dir=model_dir)

with DAG(
    'churnbuster_etl_local',
    default_args=default_args,
    description='End-to-end churn prediction pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['local', 'etl', 'ml'],
) as dag:

    # --- UPDATED TO PYTHONOPERATOR ---
    generate_data = PythonOperator(
        task_id='generate_synthetic_data',
        python_callable=generate_synthetic_data_python,
        op_kwargs={'count': 1000} # Pass the customer count as an argument
    )
    # --- Task: process_data remains the same for now ---

    process_data = BashOperator(
        task_id='process_with_spark',
        bash_command='pip install pyspark && python /opt/airflow/src/processing/process_data.py',
        env={
            'JAVA_HOME': '/usr/lib/jvm/java-17-openjdk-amd64',
            'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/lib/jvm/java-17-openjdk-amd64/bin'
        }
    )

    # --- UPDATED TASK: TRAIN MODEL ---
    # This command uses a dummy XCom push, but relies on the train_model.py script to output the version.
    # The actual XCom push will be handled by pulling the version in the next task.
    # --- UPDATED TO PYTHONOPERATOR (Train Model) ---
    train_model = PythonOperator(
        task_id='train_model',
        python_callable=train_model_python
    )

    # --- UPDATED TASK: PREDICT CHURN ---
    # We pass the full model folder path and the script will find the latest model.
    # --- UPDATED TO PYTHONOPERATOR (Predict Churn) ---
    predict_churn = PythonOperator(
        task_id='predict_churn',
        python_callable=predict_churn_python
    )

    # --- NEW TASK: SEND EMAILS ---
    send_emails = BashOperator(
        task_id='send_retention_emails',
        bash_command='python /opt/airflow/src/modeling/send_alerts.py'
    )

    # --- UPDATE DEPENDENCIES ---
    generate_data >> process_data >> train_model >> predict_churn >> send_emails