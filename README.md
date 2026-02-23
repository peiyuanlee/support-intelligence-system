# Support Intelligence System

A real-time customer support ticket processing system using Kafka, LangChain, PostgreSQL, and Apache Airflow. This system automatically analyzes incoming support tickets, extracts insights, finds similar historical tickets, and generates suggested responses using AI.

---

## **Overview**

The Support Intelligence System is a data pipeline that processes customer support tickets in real-time. It uses natural language processing and machine learning to:

- Classify ticket urgency automatically
- Analyze customer sentiment
- Find similar historical tickets using vector search
- Generate AI-powered response suggestions
- Calculate daily analytics and metrics

This system helps support teams respond faster and more consistently to customer inquiries.

---

## **Architecture**

```
┌─────────────────┐
│ Ticket Generator│ (Simulates incoming tickets)
│   (CSV/API)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka Topic    │ (Message queue)
│ support_tickets │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Kafka Consumer                │
│   (LangChain + Ollama)          │
│   ├─ Classify urgency           │
│   ├─ Extract entities           │
│   ├─ Sentiment analysis         │
│   ├─ Vector search (similar)    │
│   └─ Generate response          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │ (Store processed tickets)
└─────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│        Airflow DAGs             │
│   ├─ Daily: Update embeddings  │
│   ├─ Hourly: Analytics         │
│   └─ Weekly: Reports            │
└─────────────────────────────────┘
```

---

## **Tech Stack**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Streaming** | Apache Kafka 4.0+ | Real-time message processing |
| **Database** | PostgreSQL 15+ | Persistent data storage |
| **Orchestration** | Apache Airflow 2.8+ | Workflow scheduling |
| **LLM** | Ollama (Llama 3.2) | Local AI inference |
| **Vector DB** | ChromaDB | Semantic search |
| **Embeddings** | Sentence Transformers | Text vectorization |
| **Language** | Python 3.11 | Primary programming language |
| **Data Processing** | Pandas, NumPy | Data manipulation |

---