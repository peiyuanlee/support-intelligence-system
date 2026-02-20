-- Connect to the database
\c support_intelligence

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(100) PRIMARY KEY,
    customer_name VARCHAR(200),
    customer_email VARCHAR(200),
    subject VARCHAR(500),
    description TEXT,
    category VARCHAR(100),
    urgency VARCHAR(50),
    sentiment VARCHAR(50),
    sentiment_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'new'
);

-- Processed responses table
CREATE TABLE IF NOT EXISTS ticket_responses (
    response_id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(100) REFERENCES tickets(ticket_id),
    suggested_response TEXT,
    confidence_score DECIMAL(3,2),
    similar_ticket_ids TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics table
CREATE TABLE IF NOT EXISTS daily_analytics (
    date DATE PRIMARY KEY,
    total_tickets INTEGER,
    urgent_tickets INTEGER,
    avg_sentiment_score DECIMAL(3,2),
    top_category VARCHAR(100),
    avg_response_time_minutes DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow_user;