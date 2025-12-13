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
    tags=['local', 'etl'],
) as dag:

    generate_data = BashOperator(
        task_id='generate_synthetic_data',
        bash_command='pip install faker pandas && python /opt/airflow/src/ingestion/generate_data.py --count 1000'
    )

    process_data = BashOperator(
        task_id='process_with_spark',
        bash_command='pip install pyspark && python /opt/airflow/src/processing/process_data.py'
    )

    generate_data >> process_data