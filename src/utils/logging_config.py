"""
Comprehensive logging configuration for FoodPal application
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class FoodPalFormatter(logging.Formatter):
    """Custom formatter for FoodPal with color support"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color if terminal supports it
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            record.msg = f"[{record.request_id}] {record.msg}"
        
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    enable_file_logging: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Setup comprehensive logging for the FoodPal application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to 'logs')
        enable_file_logging: Whether to enable file logging
        max_bytes: Maximum size of log files before rotation
        backup_count: Number of backup log files to keep
    """
    
    # Create logs directory
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = FoodPalFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # File handlers if enabled
    if enable_file_logging:
        # Main application log
        app_log_file = log_dir / 'foodpal.log'
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        app_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(app_handler)
        
        # Error-only log
        error_log_file = log_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(app_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Performance log
        perf_log_file = log_dir / 'performance.log'
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        perf_handler.setFormatter(app_formatter)
        
        # Create performance logger
        perf_logger = logging.getLogger('foodpal.performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
    
    # Configure specific loggers
    configure_component_loggers()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File logging: {enable_file_logging}")
    
    if enable_file_logging:
        logger.info(f"Log files directory: {log_dir.absolute()}")

def configure_component_loggers():
    """Configure loggers for specific components"""
    
    # Database operations
    db_logger = logging.getLogger('foodpal.database')
    db_logger.setLevel(logging.INFO)
    
    # Recipe generation
    recipe_logger = logging.getLogger('foodpal.recipes')
    recipe_logger.setLevel(logging.INFO)
    
    # Background tasks
    tasks_logger = logging.getLogger('foodpal.tasks')
    tasks_logger.setLevel(logging.INFO)
    
    # API requests
    api_logger = logging.getLogger('foodpal.api')
    api_logger.setLevel(logging.INFO)
    
    # UI operations
    ui_logger = logging.getLogger('foodpal.ui')
    ui_logger.setLevel(logging.INFO)
    
    # External services (reduce verbosity)
    external_loggers = [
        'httpx', 'aiohttp', 'urllib3', 'requests',
        'sqlalchemy.engine', 'sqlalchemy.pool'
    ]
    
    for logger_name in external_loggers:
        ext_logger = logging.getLogger(logger_name)
        ext_logger.setLevel(logging.WARNING)

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, operation_name: str, logger_name: str = 'foodpal.performance'):
        self.operation_name = operation_name
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Started: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type is None:
                self.logger.info(f"Completed: {self.operation_name} in {duration:.3f}s")
            else:
                self.logger.error(f"Failed: {self.operation_name} after {duration:.3f}s - {exc_val}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the foodpal prefix"""
    return logging.getLogger(f"foodpal.{name}")

# Convenience functions for common operations
def log_database_operation(operation: str, duration: float, affected_rows: int = None):
    """Log database operation performance"""
    logger = get_logger('database')
    message = f"{operation} completed in {duration:.3f}s"
    if affected_rows is not None:
        message += f" (affected: {affected_rows} rows)"
    logger.info(message)

def log_api_request(method: str, url: str, status_code: int, duration: float):
    """Log API request performance"""
    logger = get_logger('api')
    logger.info(f"{method} {url} -> {status_code} in {duration:.3f}s")

def log_recipe_generation(recipe_count: int, duration: float, success_count: int):
    """Log recipe generation performance"""
    logger = get_logger('recipes')
    logger.info(f"Generated {success_count}/{recipe_count} recipes in {duration:.3f}s")

def log_ui_operation(operation: str, user_id: int, duration: float = None):
    """Log UI operation"""
    logger = get_logger('ui')
    message = f"User {user_id}: {operation}"
    if duration is not None:
        message += f" ({duration:.3f}s)"
    logger.info(message)