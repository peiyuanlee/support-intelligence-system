#!/bin/bash

# This needs to run as postgres superuser
psql -U postgres << EOF
CREATE DATABASE support_intelligence;
CREATE USER airflow_user WITH PASSWORD 'airflow_pass';
GRANT ALL PRIVILEGES ON DATABASE support_intelligence TO airflow_user;

-- Connect to the new database and grant schema privileges
\c support_intelligence
GRANT ALL PRIVILEGES ON SCHEMA public TO airflow_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO airflow_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO airflow_user;
EOF

echo "Database and user created successfully"

psql -U airflow_user -d support_intelligence -f scripts/db_init.sql

echo "Tables created successfully"