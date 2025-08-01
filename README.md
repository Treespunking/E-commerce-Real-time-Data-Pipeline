# E-commerce Real-time Data Pipeline 

## Project Architecture

This project implements a complete real-time data pipeline for e-commerce event processing using modern big data technologies. The architecture follows a lambda/kappa pattern with streaming ingestion, processing, and storage in a data lakehouse format.

### Technology Stack
- **Message Broker**: Apache Kafka (Confluent Platform)
- **Stream Processing**: Apache Spark Structured Streaming
- **Storage**: Apache Iceberg (Data Lakehouse)
- **Cloud Storage**: Amazon S3
- **API Gateway**: FastAPI
- **Orchestration**: Docker Compose
- **Coordination**: Apache Zookeeper

## Component Breakdown

### 1. Infrastructure Layer (docker-compose.yml)

**Zookeeper Service**
- Manages Kafka cluster coordination
- Runs on port 2181
- Essential for Kafka broker discovery and metadata management

**Kafka Broker**
- Confluent Kafka image (version 7.0.0)
- Single broker setup with replication factor 1 (development configuration)
- Exposed on port 9092
- Configured with PLAINTEXT security for simplicity
- Topic auto-creation enabled with proper retention policies

**Kafka Topic Initialization**
- Automated topic creation service (`kafka-init`)
- Creates `ecommerce_events` topic with 1 partition
- Ensures Kafka readiness before proceeding
- Uses Python socket testing for robust health checks

**Spark Streaming Service**
- Bitnami Spark 3.5.2 image
- Includes comprehensive package dependencies:
  - Kafka integration: `spark-sql-kafka-0-10_2.12:3.5.2`
  - Iceberg support: `iceberg-spark-runtime-3.5_2.12:1.5.2`
  - AWS S3 integration: `hadoop-aws:3.3.4`
- Automatic job submission with proper configuration
- Environment variable integration for S3 credentials

**FastAPI Service**
- Custom-built API service
- Event ingestion endpoint
- Kafka producer integration
- Health check and dependency management

### 2. Data Ingestion Layer (main.py - FastAPI)

**Event API Characteristics**
- RESTful endpoint (`/events`) for real-time event ingestion
- Pydantic models for data validation and serialization
- Flexible schema with `extra='allow'` for dynamic event properties
- Confluent Kafka producer for reliable message delivery

**Event Model Structure**
```python
- event_id: Unique identifier for deduplication
- event_type: Categorizes events (page_view, add_to_cart, purchase, etc.)
- user_id: Customer identifier
- session_id: Session tracking (used as Kafka partition key)
- location: Geographic information
- device: Device type tracking
- timestamp: ISO8601 formatted timestamp
- Additional dynamic fields based on event type
```

**Kafka Integration**
- Asynchronous message production
- Session-based partitioning for ordered processing
- Delivery confirmation callbacks
- Error handling and retry mechanisms

### 3. Stream Processing Layer (spark_streaming.py)

**Spark Session Configuration**
- Iceberg catalog integration with Hadoop-compatible storage
- S3A filesystem configuration with AWS credential chain
- Schema evolution and fanout write support
- Optimized for streaming workloads

**Data Schema Management**
- Comprehensive schema definition covering all e-commerce event types
- Permissive JSON parsing to handle schema variations
- Data quality validation with null handling
- Invalid record logging for monitoring

**Stream Processing Pipeline**
1. **Ingestion**: Kafka stream reader with automatic offset management
2. **Parsing**: JSON deserialization with error handling
3. **Transformation**: Timestamp conversion and date partitioning
4. **Validation**: Data quality checks and cleansing
5. **Storage**: Iceberg table writes with ACID guarantees

**Iceberg Table Design**
- Partitioned by `event_type` and `event_date` for query optimization
- Schema evolution enabled for backward compatibility
- S3-based storage with configurable warehouse location
- Streaming checkpoints for fault tolerance

### 4. Storage Layer (Apache Iceberg + S3)

**Data Lakehouse Benefits**
- ACID transactions for data consistency
- Time travel capabilities for historical analysis
- Schema evolution without breaking downstream consumers
- Efficient query performance with file pruning
- Multi-engine compatibility (Spark, Trino, Flink)

**Partitioning Strategy**
- **Event Type Partitioning**: Enables efficient filtering by event category
- **Date Partitioning**: Optimizes temporal queries and data lifecycle management
- **S3 Layout**: Organized structure for cost-effective storage and retrieval

## Data Flow Architecture

### Real-time Processing Flow
1. **Event Generation**: Client applications send events to FastAPI endpoint
2. **Message Queuing**: Events are published to Kafka topic with session-based partitioning
3. **Stream Processing**: Spark Structured Streaming continuously processes Kafka messages
4. **Data Transformation**: Events are parsed, validated, and enriched with metadata
5. **Storage**: Clean data is written to Iceberg tables in S3 with ACID guarantees
6. **Query Layer**: Data is immediately available for analytics and reporting

### Key Features

**Scalability**
- Horizontal scaling through Kafka partitioning
- Spark cluster scaling for increased throughput
- S3 storage scaling without limits
- Container-based deployment for cloud portability

**Reliability**
- Kafka message durability and replication
- Spark streaming checkpoints for fault recovery
- Iceberg ACID transactions prevent data corruption
- Comprehensive error handling and logging

**Flexibility**
- Schema evolution without service interruption
- Dynamic event properties support
- Multi-format data ingestion capabilities
- Pluggable storage backends

**Performance**
- Stream processing with sub-second latency
- Optimized Iceberg file formats (Parquet/ORC)
- Intelligent partitioning for query acceleration
- Configurable batch intervals and buffer sizes

## Operational Considerations

### Monitoring and Observability
- Kafka metrics for throughput and lag monitoring
- Spark streaming UI for job monitoring
- Application logging for debugging and auditing
- Invalid record tracking for data quality assessment

### Security
- AWS IAM integration for S3 access control
- Kafka security can be enhanced with SASL/SSL
- Network isolation through Docker networking
- Environment variable management for secrets

### Disaster Recovery
- Kafka topic replication (configurable)
- S3 cross-region replication capabilities
- Iceberg snapshot and rollback features
- Automated backup strategies

## Use Cases

This pipeline architecture supports various e-commerce analytics scenarios:

- **Real-time Dashboards**: Customer behavior tracking and KPI monitoring
- **Personalization**: ML feature engineering for recommendation systems
- **Fraud Detection**: Real-time anomaly detection on transaction patterns
- **Marketing Analytics**: Campaign effectiveness and customer journey analysis
- **Inventory Management**: Demand forecasting and stock optimization
- **Customer Support**: Session replay and troubleshooting capabilities





