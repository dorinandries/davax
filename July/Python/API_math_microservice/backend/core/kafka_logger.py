import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from kafka import KafkaProducer
import json

def get_kafka_logger(log_days: int = 1):
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    logs_dir = os.path.abspath(logs_dir)
    os.makedirs(logs_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    dated_folder = os.path.join(logs_dir, today)
    os.makedirs(dated_folder, exist_ok=True)
    log_file = os.path.join(dated_folder, "kafka_logs.log")

    handler = TimedRotatingFileHandler(
        log_file, when="D", interval=log_days, backupCount=30, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("kafka_logger")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger

class KafkaLogger:
    def __init__(self, topic, bootstrap_servers):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self._producer = None
        self.logger = get_kafka_logger()

    @property
    def producer(self):
        if self._producer is None:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    acks="all"
                )
            except Exception as e:
                self.logger.error(f"Failed to connect to Kafka: {e}")
                raise
        return self._producer

    def log(self, message: dict):
        try:
            self.producer.send(self.topic, message)
            self.producer.flush()
            self.logger.info(f"Sent to Kafka: {message}")
        except Exception as e:
            self.logger.error(f"Kafka send error: {e} | Message: {message}")