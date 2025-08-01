from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp, date_format
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
    BooleanType, MapType, TimestampType
)
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Read S3 bucket name from environment variable ===
# No need for python-dotenv if using docker-compose env_file
iceberg_s3_bucket = os.getenv("ICEBERG_S3_BUCKET")
if not iceberg_s3_bucket:
    raise ValueError("❌ Environment variable 'ICEBERG_S3_BUCKET' is not set. Please define it in your .env file.")

# Define S3 paths
warehouse_path = f"s3a://{iceberg_s3_bucket}/iceberg-warehouse"
checkpoint_location = f"s3a://{iceberg_s3_bucket}/checkpoint/ecommerce-stream"
table_location = f"{warehouse_path}/db/ecommerce_events"

# === Initialize Spark Session with Iceberg + S3 Support ===
spark = SparkSession.builder \
    .appName("KafkaEcommerceStreaming") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", warehouse_path) \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
    .config("spark.hadoop.fs.s3a.fast.upload", "true") \
    .getOrCreate()

# Reduce logging noise
spark.sparkContext.setLogLevel("WARN")

# === Switch to the 'local' catalog and create database ===
try:
    spark.sql("CREATE DATABASE IF NOT EXISTS local.db")
    logger.info(f"✅ Successfully switched to catalog 'local' and ensured database 'db' exists.")
    logger.info(f"📁 Iceberg warehouse: {warehouse_path}")
except Exception as e:
    logger.error(f"❌ Failed to create database in Iceberg catalog: {e}")
    spark.stop()
    raise

# === Define Base Schema ===
ecommerce_base_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("user_id", IntegerType(), True),
    StructField("product_id", StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("location", StringType(), True),
    StructField("device", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("category", StringType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("price", DoubleType(), True),
    StructField("order_id", StringType(), True),
    StructField("amount", DoubleType(), True),
])

# === Read from Kafka ===
try:
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "ecommerce_events") \
        .load()
    logger.info("✅ Connected to Kafka topic 'ecommerce_events'.")
except Exception as e:
    logger.error(f"❌ Failed to read from Kafka: {e}")
    spark.stop()
    raise

# === Parse JSON with permissive mode ===
parsed_df = df.select(
    from_json(col("value").cast("string"), ecommerce_base_schema, {"mode": "PERMISSIVE"}).alias("data")
).select("data.*")

# Add processed timestamp and partition date
parsed_df = parsed_df \
    .withColumn("timestamp", to_timestamp(col("timestamp"))) \
    .withColumn("event_date", date_format(col("timestamp"), "yyyy-MM-dd"))

# === Data Quality: Drop nulls on critical fields ===
required_fields = ["event_id", "event_type", "user_id", "timestamp"]
cleaned_df = parsed_df.dropna(subset=required_fields)

# Optional: Log invalid records to console
invalid_df = parsed_df.filter(col("event_id").isNull() | col("event_type").isNull())
invalid_query = invalid_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .queryName("invalid_records_console") \
    .start()

logger.info("✅ Streaming query started for invalid records (logged to console).")

# === Create Iceberg Table (if not exists) with explicit S3 location ===
try:
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS local.db.ecommerce_events (
            event_id STRING,
            event_type STRING,
            user_id INT,
            product_id STRING,
            session_id STRING,
            location STRING,
            device STRING,
            timestamp TIMESTAMP,
            event_date STRING,
            ip_address STRING,
            category STRING,
            quantity INT,
            price DOUBLE,
            order_id STRING,
            amount DOUBLE
        )
        USING iceberg
        LOCATION '{table_location}'
        PARTITIONED BY (event_type, event_date)
    """)
    logger.info("✅ Iceberg table 'local.db.ecommerce_events' created or already exists.")
    logger.info(f"📌 Table location: {table_location}")
except Exception as e:
    logger.error(f"❌ Failed to create Iceberg table: {e}")
    spark.stop()
    raise

# === Enable Schema Evolution & Fanout Writes ===
spark.conf.set("spark.sql.iceberg.schema.auto.add.columns", "true")
spark.conf.set("spark.sql.iceberg.handle.fanout.write", "true")
logger.info("✅ Enabled schema evolution and fanout write support.")

# === Reorder columns to match Iceberg table schema exactly ===
cleaned_df = cleaned_df.select(
    "event_id",
    "event_type",
    "user_id",
    "product_id",
    "session_id",
    "location",
    "device",
    "timestamp",
    "event_date",
    "ip_address",
    "category",
    "quantity",
    "price",
    "order_id",
    "amount"
)

# === Write Stream to Iceberg ===
try:
    query = cleaned_df.writeStream \
        .outputMode("append") \
        .format("iceberg") \
        .queryName("iceberg_stream_writer") \
        .option("checkpointLocation", checkpoint_location) \
        .toTable("local.db.ecommerce_events")

    logger.info(f"✅ Streaming query started: writing to Iceberg table 'local.db.ecommerce_events'.")
    logger.info(f"🔁 Checkpoint location: {checkpoint_location}")

    # Wait for termination
    spark.streams.awaitAnyTermination()

except Exception as e:
    logger.error(f"❌ Streaming query failed: {e}")
    raise

finally:
    # Clean shutdown
    spark.stop()