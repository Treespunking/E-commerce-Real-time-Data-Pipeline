from confluent_kafka import Consumer

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'test-group',
    'auto.offset.reset': 'earliest',
    'socket.timeout.ms': 10000,
    'api.version.request.timeout.ms': 10000
}

try:
    c = Consumer(conf)
    metadata = c.list_topics(timeout=10)
    print("🎉 Success! Connected to Kafka")
    print("Topics:", list(metadata.topics.keys()))
    c.close()
except Exception as e:
    print("❌ Failed to connect:", e)