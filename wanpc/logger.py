"""Logging utilities for wanpc."""

import logging
from typing import Optional

LOGGER_NAME = "wanpc"

def get_logger() -> logging.Logger:
    """
    Get the global logger instance.
    
    Returns:
        The global logger instance
    """
    return logging.getLogger(LOGGER_NAME)


def set_verbose(verbose: bool) -> None:
    """
    Set logging level based on the verbose flag.
    
    Args:
        verbose: Whether to show verbose output
    """
    logger = get_logger()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging with the specified level and optional log file.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        
    Returns:
        The configured logger instance
    """
    logger = get_logger()
    
    # Reset handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set level (default to INFO for invalid levels)
    if level not in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
        level = logging.INFO
    logger.setLevel(level)
    
    # Add stream handler
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # Add file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, IOError):
            # Log but don't fail if file handler creation fails
            logger.warning(f"Failed to create log file: {log_file}")
    
    return logger
