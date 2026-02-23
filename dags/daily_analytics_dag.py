from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

default_args = {
    'owner': 'support_team',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def calculate_daily_metrics(**context):
    hook = PostgresHook(postgres_conn_id = 'postgres_support')
    conn = hook.get_conn()
    curr = conn.cursor()

    execution_date = context['execution_date'].date()
    
    curr.execute(
        """
        INSERT INTO daily_analytics
        (date, total_tickets, urgent_tickets, avg_sentiment_score, top_category, avg_response_time_minutes)
        SELECT 
            %s as date,
            COUNT(*) as total_tickets,
            SUM(CASE WHEN urgency IN ('urgent', 'high') THEN 1 ELSE 0 END),
            AVG(sentiment_score) as avg_sentiment_score,
            MODE() WITHIN GROUP (ORDER BY category) as top_category
            AVG(EXTRACT(EPOCH FROM (processed_at - created_at))/60) as avg_response_time_minutes
        FROM tickets
        WHERE DATE(created_at) = %s
        ON CONFLICT (date) DO UPDATE SET
            total_tickets = EXCLUDED.total_tickets,
            urgent_tickets = EXCLUDED.urgent_tickets,
            avg_sentiment_score = EXCLUDED.avg_sentiment_score,
            top_category = EXCLUDED.top_category.
            avg_response_time_minutes = EXCLUDED.avg_response_time_minutes
        """, (execution_date, execution_date)
    )
    conn.commit()
    curr.close()
    conn.close()
    print(f"Daily metrics calculated for {execution_date}")

with DAG(
    dag_id = 'support_daily_analytics',
    default_args = default_args,
    description = 'Calculate daily support metrics',
    schedule_interval = '@daily',
    start_date = datetime(2024,1,1),
    catchup = False,
    tags = ['analytics', 'support'],
) as dag:
    calculate_metrics = PythonOperator(
        task_id = 'calculate_daily_metrics',
        python_callable = calculate_daily_metrics,
    )
    generate_report = PostgresOperator(
        task_id = 'generate_daily_report',
        postgres_conn_id = 'postgres_support',
        sql = """
            SELECT date, total_tickets, urgent_tickets,
            ROUND(avg_sentiment_score,2) as avg_sentiment,
            top_category
            FROM daily_analytics
            WHERFE date = CURRENT_DATE - INTERVAL '1 day'
            """
    )

calculate_metrics >> generate_report