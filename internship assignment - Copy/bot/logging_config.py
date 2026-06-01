"""
Logging configuration module.
Sets up application-wide logging with file rotation, structured logging, and security safeguards.
"""

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class CredentialFilter(logging.Filter):
    """Filter to prevent credential leakage in logs."""
    
    SENSITIVE_KEYWORDS = [
        'api_key', 'api_secret', 'password', 'token', 'secret',
        'credential', 'auth', 'X-MBX-APIKEY'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records to remove sensitive information.
        
        Args:
            record (logging.LogRecord): Log record to filter.
        
        Returns:
            bool: Always True (we sanitize instead of blocking).
        """
        # Sanitize message
        message = record.getMessage()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword.lower() in message.lower():
                message = self._sanitize_message(message)
                record.msg = message
                record.args = ()
        
        return True
    
    @staticmethod
    def _sanitize_message(message: str) -> str:
        """Replace sensitive values with masked values."""
        import re
        # Mask API keys and secrets
        message = re.sub(r'(?i)(api[_-]?key[=:]\s*)[\w\d]+', r'\1***MASKED***', message)
        message = re.sub(r'(?i)(api[_-]?secret[=:]\s*)[\w\d]+', r'\1***MASKED***', message)
        message = re.sub(r'(?i)(X-MBX-APIKEY[=:]\s*)[\w\d]+', r'\1***MASKED***', message)
        return message


class StructuredFormatter(logging.Formatter):
    """Formatter for structured logging output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured information."""
        # Build timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message with optional request ID
        msg = record.getMessage()
        
        # Format: TIMESTAMP | LEVEL | LOGGER | MESSAGE
        return f"{timestamp} | {record.levelname:8s} | {record.name:12s} | {msg}"


def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    enable_console: bool = True
) -> logging.Logger:
    """
    Configure application-wide logging with rotation and security.
    
    Logs are written to a file with rotation based on file size.
    Each log entry includes timestamp, log level, logger name, and descriptive message.
    Sensitive information is automatically masked to prevent credential leakage.
    
    Args:
        log_dir (str): Directory where log files will be stored. Defaults to 'logs'.
        log_level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to INFO.
        max_bytes (int): Maximum log file size before rotation. Defaults to 10MB.
        backup_count (int): Number of backup log files to keep. Defaults to 5.
        enable_console (bool): Whether to output to console. Defaults to True.
    
    Returns:
        logging.Logger: Configured logger instance.
    
    Raises:
        Exception: If log directory cannot be created.
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    try:
        log_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise Exception(f"Failed to create log directory '{log_dir}': {str(e)}")
    
    # Create logger
    logger = logging.getLogger("TradingBot")
    logger.setLevel(log_level)
    logger.propagate = False
    
    # Remove existing handlers to prevent duplicate logs
    logger.handlers.clear()
    
    # Create credential filter
    cred_filter = CredentialFilter()
    
    # Create formatter
    formatter = StructuredFormatter()
    
    # File handler with rotation
    try:
        log_file = log_path / "trading.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(cred_filter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create rotating file handler: {str(e)}")
    
    # Console handler (for warnings and errors only)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(cred_filter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """
    Get the configured logger instance.
    
    Returns:
        logging.Logger: The trading bot logger.
    """
    logger = logging.getLogger("TradingBot")
    
    # Ensure logger has at least one handler
    if not logger.handlers:
        # If no handlers, add a null handler to prevent errors
        logger.addHandler(logging.NullHandler())
    
    return logger


def get_log_file_size(log_dir: str = "logs") -> int:
    """
    Get the current size of the log file in bytes.
    
    Args:
        log_dir (str): Log directory path.
    
    Returns:
        int: Size in bytes, or 0 if file doesn't exist.
    """
    log_file = Path(log_dir) / "trading.log"
    if log_file.exists():
        return log_file.stat().st_size
    return 0


def get_log_file_count(log_dir: str = "logs") -> int:
    """
    Get the number of log files (including rotated backups).
    
    Args:
        log_dir (str): Log directory path.
    
    Returns:
        int: Number of log files.
    """
    log_dir_path = Path(log_dir)
    if not log_dir_path.exists():
        return 0
    
    log_files = list(log_dir_path.glob("trading.log*"))
    return len(log_files)

