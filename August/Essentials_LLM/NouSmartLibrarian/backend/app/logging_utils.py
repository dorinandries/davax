from loguru import logger
from datetime import datetime
from pathlib import Path
import json


def _log_dir(base: str) -> Path:
    today = datetime.now().strftime('%d-%m-%Y')
    root = Path("logs") / today
    (root / base).mkdir(parents=True, exist_ok=True)
    return root


def app_logger():
    log_root = _log_dir("")
    app_path = log_root / "app.log"
    logger.add(app_path, rotation="10 MB", retention="14 days", enqueue=True)
    return logger


class TokensLogger:
    def __init__(self):
        self.root = _log_dir("tokens")
        self.file = self.root / "tokens.log"
        self.file.touch(exist_ok=True)


    def log(self, record: dict):
        with self.file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")