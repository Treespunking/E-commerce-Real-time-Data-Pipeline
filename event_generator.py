from faker import Faker
from faker.providers import address, company, date_time, internet, lorem, phone_number
import random
import json
import time
import requests

# Initialize Faker
fake = Faker()
fake.add_provider(address)
fake.add_provider(date_time)
fake.add_provider(internet)
fake.add_provider(lorem)
fake.add_provider(phone_number)
fake.add_provider(company)

# FastAPI endpoint
FASTAPI_URL = "http://localhost:8000/events"

# Event Types
event_types = ["login", "product_view", "add_to_cart", "checkout", "payment_success", "payment_failure"]

def generate_event():
    event_type = random.choice(event_types)
    base = {
        "event_id": fake.uuid4(),
        "event_type": event_type,
        "user_id": fake.random_int(min=1000, max=999999),
        "timestamp": fake.iso8601(),
        "session_id": fake.uuid4(),
        "location": fake.city(),
        "device": random.choice(["desktop", "mobile", "tablet"])
    }

    if event_type == "login":
        base.update({
            "ip_address": fake.ipv4(),
            "login_method": random.choice(["email_password", "google", "facebook"]),
            "user_agent": fake.user_agent(),
            "success": random.choice([True, False])
        })

    elif event_type == "product_view":
        base.update({
            "product_id": f"P{fake.random_int(min=1000, max=9999)}",
            "category": random.choice(["electronics", "clothing", "books", "home"]),
            "search_query": fake.word(),
            "referrer": random.choice(["homepage", "search", "email", "ads"]),
            "duration_seconds": fake.random_int(min=10, max=300)
        })

    elif event_type == "add_to_cart":
        base.update({
            "product_id": f"P{fake.random_int(min=1000, max=9999)}",
            "quantity": fake.random_int(min=1, max=5),
            "price": round(random.uniform(10, 500), 2),
            "cart_id": fake.uuid4(),
            "was_wishlist_item": random.choice([True, False])
        })

    elif event_type == "checkout":
        base.update({
            "cart_id": fake.uuid4(),
            "total_items": fake.random_int(min=1, max=10),
            "total_value": round(random.uniform(50, 1000), 2),
            "shipping_address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "zip": fake.zipcode()
            },
            "payment_method_selected": random.choice(["credit_card", "paypal", "apple_pay"])
        })

    elif event_type in ["payment_success", "payment_failure"]:
        base.update({
            "order_id": fake.uuid4(),
            "cart_id": fake.uuid4(),
            "amount": round(random.uniform(50, 1000), 2),
            "payment_method": random.choice(["credit_card", "paypal", "apple_pay"]),
            "transaction_id": fake.uuid4()
        })
        if event_type == "payment_failure":
            base["failure_reason"] = random.choice(["insufficient_funds", "invalid_card", "network_error"])

    return base

def send_event(event):
    try:
        response = requests.post(FASTAPI_URL, json=event)
        print(f"Sent event: {event['event_type']} | Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send event: {e}")

# Main loop
if __name__ == "__main__":
    print("Starting event generator...")
    while True:
        event = generate_event()
        send_event(event)
        time.sleep(0.1)  # ~10 events per second