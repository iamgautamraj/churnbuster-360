from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'churnbuster',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'churnbuster_etl_local',
    default_args=default_args,
    description='End-to-end churn prediction pipeline',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['local', 'etl', 'ml'],
) as dag:

    generate_data = BashOperator(
        task_id='generate_synthetic_data',
        bash_command='pip install faker pandas && python /opt/airflow/src/ingestion/generate_data.py --count 1000'
    )

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
    train_model = BashOperator(
        task_id='train_model',
        bash_command='pip install scikit-learn pandas pyarrow && python /opt/airflow/src/modeling/train_model.py'
    )

    # --- UPDATED TASK: PREDICT CHURN ---
    # We pass the full model folder path and the script will find the latest model.
    predict_churn = BashOperator(
        task_id='predict_churn',
        # We pass the model directory as an argument
        bash_command='python /opt/airflow/src/modeling/predict.py --model-dir /opt/airflow/data/model/'
    )

    # --- NEW TASK: SEND EMAILS ---
    send_emails = BashOperator(
        task_id='send_retention_emails',
        bash_command='python /opt/airflow/src/modeling/send_alerts.py'
    )

    # --- UPDATE DEPENDENCIES ---
    generate_data >> process_data >> train_model >> predict_churn >> send_emails