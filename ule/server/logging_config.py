import logging
import sys
import json
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configures structured JSON logging for production."""
    logger = logging.getLogger("ule_server")
    logger.setLevel(logging.INFO)
    
    # Use stdout for logs (cloud-native friendly)
    logHandler = logging.StreamHandler(sys.stdout)
    
    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    
    return logger

# Singleton logger
logger = setup_logging()
