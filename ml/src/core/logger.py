# ml-service/src/utils/logger.py
import logging
import sys
import os

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a logger instance.
    """
    logger_instance = logging.getLogger(name)
    
    # Prevent adding multiple handlers if logger is already configured
    if logger_instance.hasHandlers():
        logger_instance.handlers.clear()

    logger_instance.setLevel(level)

    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)

    # Create formatter
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'
    formatter = logging.Formatter(log_format)
    ch.setFormatter(formatter)

    # Add handler to logger
    logger_instance.addHandler(ch)
    
    # Set propagate to False to avoid duplicate logs if root logger is also configured
    logger_instance.propagate = False

    return logger_instance

# Example of how to use it in other files:
# from .logger import setup_logger # Or appropriate relative import
# logger = setup_logger(__name__)
#
# logger.info("This is an info message from ML service.")
# logger.warning("This is a warning.")
# try:
#   raise ValueError("A sample error")
# except ValueError as e:
#   logger.error("An error occurred in ML service", exc_info=True) # exc_info=True logs stack trace