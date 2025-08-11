from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    "api_requests",  # Use the topic name you configured
    # bootstrap_servers="kafka:9092",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

print("Listening for messages on 'api_requests' topic...")
for msg in consumer:
    print(msg.value)