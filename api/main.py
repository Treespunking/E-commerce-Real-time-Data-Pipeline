from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from confluent_kafka import Producer
import json
import time

app = FastAPI()

# Kafka configuration
conf = {
    'bootstrap.servers': 'kafka:9092'
}
producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# Request model - now includes event_id and timestamp
class EventModel(BaseModel):
    event_id: str
    event_type: str
    user_id: int
    session_id: str
    location: str
    device: str
    timestamp: str  # ISO8601 format from faker

    # Allow any additional fields (e.g., product_id, cart_id, etc.)
    class Config:
        extra = 'allow'  # Allows dynamic fields based on event type

@app.post("/events")
async def send_event(event: EventModel):
    event_dict = event.dict()

    try:
        producer.produce(
            'ecommerce_events',
            key=event_dict["session_id"],
            value=json.dumps(event_dict),
            callback=delivery_report
        )
        producer.poll(0)  # Trigger delivery callbacks
        return {"status": "Event sent", "event": event_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send event: {e}")