
import logging, sys

def app_logger():
    logger = logging.getLogger("smart_librarian")
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stdout)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
