# settings.py
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    db_path: str = "math_results.db"
    log_level: str = "INFO"
    # kafka_bootstrap_servers: str = "kafka:9092"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "api_requests"
