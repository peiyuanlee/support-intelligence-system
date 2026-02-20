from airflow import settings
from airflow.models import Connection
import os

def create_postgres_connection():
    """Create PostgreSQL connection in Airflow"""
    conn = Connection(
        conn_id='postgres_support',
        conn_type='postgres',
        host='localhost',
        schema='support_intelligence',
        login='airflow_user',
        password='airflow_pass',
        port=5432
    )
    
    session = settings.Session()
    
    # Check if connection exists
    existing = session.query(Connection).filter(
        Connection.conn_id == conn.conn_id
    ).first()
    
    if existing:
        session.delete(existing)
    
    session.add(conn)
    session.commit()
    print(f"Connection {conn.conn_id} created successfully")

if __name__ == "__main__":
    create_postgres_connection()