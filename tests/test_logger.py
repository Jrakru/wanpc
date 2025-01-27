"""Tests for the logger module."""
import logging
import pytest
from wanpc.logger import setup_logging

def test_setup_logging(tmp_path):
    """Test setting up logging."""
    # Test with default level
    logger = setup_logging()
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0
    
    # Test with custom level
    logger = setup_logging(level=logging.DEBUG)
    assert logger.level == logging.DEBUG
    
    # Test with log file
    log_file = tmp_path / "test.log"
    logger = setup_logging(log_file=log_file)
    assert len(logger.handlers) > 1  # Should have both stream and file handlers
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    
    # Test log message
    test_message = "Test log message"
    logger.info(test_message)
    assert log_file.exists()
    log_content = log_file.read_text()
    assert test_message in log_content

def test_setup_logging_invalid_level():
    """Test setup_logging with invalid level."""
    # Should default to INFO if invalid level is provided
    logger = setup_logging(level=999)
    assert logger.level == logging.INFO

def test_setup_logging_invalid_file(tmp_path):
    """Test setup_logging with invalid log file."""
    # Should still work with stream handler if file handler fails
    invalid_path = tmp_path / "nonexistent" / "test.log"
    logger = setup_logging(log_file=invalid_path)
    assert len(logger.handlers) > 0
    assert all(isinstance(h, logging.StreamHandler) for h in logger.handlers)
