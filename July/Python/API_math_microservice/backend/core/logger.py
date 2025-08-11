import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logging(settings, log_days: int = 1):
    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    logs_dir = os.path.abspath(logs_dir)
    os.makedirs(logs_dir, exist_ok=True)

    # Log file path with date in folder name
    today = datetime.now().strftime("%Y-%m-%d")
    dated_folder = os.path.join(logs_dir, today)
    os.makedirs(dated_folder, exist_ok=True)
    log_file = os.path.join(dated_folder, "requests.log")

    # Remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(
        log_file, when="D", interval=log_days, backupCount=30, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    
    # Set up custom logger
    logger = logging.getLogger("api")
    logger.setLevel(settings.log_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    # Set up root logger to use the same handler
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.propagate = False
    return logger
