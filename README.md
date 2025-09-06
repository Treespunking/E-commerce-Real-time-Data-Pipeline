# E-Commerce Event Streaming with Kafka & Iceberg

A real-time data pipeline that simulates user activity, streams events via **Apache Kafka**, and lands them into **Apache Iceberg on S3** for analytics. Built with FastAPI, Spark Structured Streaming, and Docker Compose for end-to-end streaming data architecture.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Kafka](https://img.shields.io/badge/Stream-Apache_Kafka-red)
![Spark](https://img.shields.io/badge/Processing-Apache_Spark-orange)
![Iceberg](https://img.shields.io/badge/Sink-Apache_Iceberg-brightgreen)

---

## Features
- Simulates realistic e-commerce user events using **Faker**
- Ingests events via **FastAPI** into **Kafka** topics
- Streams and processes data using **Spark Structured Streaming**
- Stores data in **Apache Iceberg** with partitioning and schema evolution
- Supports **S3-compatible storage** (e.g., AWS, MinIO)
- Fully containerized with **Docker Compose**
- Includes data quality checks and console logging for invalid records
- Schema auto-evolution and fanout write support enabled

---

## Requirements
- Docker and Docker Compose
- S3-compatible storage (AWS S3 recommended)
- AWS credentials configured (via IAM or environment)
- Python 3.8+ (for local testing)
- `python-dotenv` (if using `.env` file)

---

## Setup & Installation

### 1. Clone the repo
```bash
git clone https://github.com/Treespunking/E-commerce-Real-time-Data-Pipeline.git
cd E-commerce-Real-time-Data-Pipeline
```

### 2. Configure environment
Create a `.env` file with your S3 bucket and AWS credentials:

```env
ICEBERG_S3_BUCKET=your-iceberg-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

> Never commit this file! It should be in `.gitignore`.

### 3. Start the full stack
```bash
docker-compose up --build
```

This will:
- Start Zookeeper and Kafka
- Create the `ecommerce_events` topic
- Launch the FastAPI ingestion endpoint
- Submit the Spark job to stream into Iceberg

---

## Simulate Real-Time Events

Once the stack is running, generate sample events:

```bash
python event_generator.py
```

> Events are sent to `http://localhost:8000/events` and streamed into Kafka → Spark → Iceberg.

---

## Data Flow Overview

```
[Faker Events] 
     ↓
[FastAPI Server] → POST /events
     ↓
[Kafka Topic: ecommerce_events]
     ↓
[Spark Structured Streaming]
     ↓
[Apache Iceberg Table (S3)]
```

### Iceberg Table Details
- **Table**: `local.db.ecommerce_events`
- **Location**: `s3a://<your-bucket>/iceberg-warehouse/db/ecommerce_events`
- **Partitioned by**: `event_type`, `event_date`
- **Checkpointing**: Enabled for fault tolerance

---

## Test Kafka Connectivity

Verify Kafka is working:

```bash
python test_kafka.py
```

Expected output:
```
Success! Connected to Kafka
Topics: ['ecommerce_events', ...]
```

---

## Explore the Data

After streaming events, explore your Iceberg table directly using **Spark SQL** or connect with tools like:
- **AWS Athena** (for querying)
- **Trino/Presto** (for federated queries)
- **Jupyter Notebook** with PySpark

Example query in Spark:
```sql
SELECT event_type, COUNT(*) FROM local.db.ecommerce_events GROUP BY event_type;
```

---

## Project Structure

```
pipeline/
│
├── docker-compose.yml         # Orchestration of all services
├── .env                       # Environment variables (S3 bucket, AWS keys)
│
├── api/
│   ├── main.py                # FastAPI endpoint to ingest events
│   ├── requirements.txt       # FastAPI & Kafka deps
│   └── Dockerfile             # API container
│
├── spark_streaming.py         # Spark job: reads Kafka, writes to Iceberg
├── event_generator.py         # Generates fake e-commerce events
├── test_kafka.py              # Test script for Kafka connectivity
│
└── spark-apps/                # Mounted volume for Spark jobs
    └── spark_streaming.py
```

---

## Key Configuration Notes

- **Schema Evolution**: Enabled via `spark.sql.iceberg.schema.auto.add.columns`
- **Fanout Writes**: Enabled to support multiple writers
- **Checkpointing**: Ensures exactly-once processing
- **PERMISSIVE JSON Parsing**: Invalid fields are set to `null` instead of failing
- **S3 Integration**: Uses `hadoop-aws` and `S3AFileSystem`

---
