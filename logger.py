"""
Logging System for MyOffer Monitor
Provides structured, professional logging capabilities
"""

import logging
import logging.handlers
import logging.config
from pathlib import Path
from datetime import datetime
from typing import Optional
import traceback
import sys

try:
    from config import LOGGING_CONFIG, LOGS_DIR, app_settings
except ImportError:
    # Fallback if config not available
    LOGS_DIR = Path("logs")
    LOGS_DIR.mkdir(exist_ok=True)
    LOGGING_CONFIG = None
    app_settings = None

# ============================================================================
# LOGGER SETUP
# ============================================================================

def setup_logging():
    """Initialize the logging system"""
    if LOGGING_CONFIG:
        logging.config.dictConfig(LOGGING_CONFIG)
    else:
        # Fallback basic configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.handlers.RotatingFileHandler(
                    LOGS_DIR / 'mom.log',
                    maxBytes=10485760,
                    backupCount=5
                )
            ]
        )
    
    # Set level from settings if available
    if app_settings and hasattr(app_settings, 'log_level'):
        level = getattr(logging, app_settings.log_level, logging.INFO)
        logging.getLogger().setLevel(level)

# ============================================================================
# CUSTOM LOGGER CLASS
# ============================================================================

class AppLogger:
    """Enhanced logger with additional convenience methods"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        self.logger.debug(self._format_message(message, kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        self.logger.info(self._format_message(message, kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        self.logger.warning(self._format_message(message, kwargs))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details"""
        full_message = self._format_message(message, kwargs)
        if exception:
            full_message += f"\nException: {str(exception)}"
            full_message += f"\nTraceback: {traceback.format_exc()}"
        self.logger.error(full_message)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception details"""
        full_message = self._format_message(message, kwargs)
        if exception:
            full_message += f"\nException: {str(exception)}"
            full_message += f"\nTraceback: {traceback.format_exc()}"
        self.logger.critical(full_message)
    
    def scan_start(self, client: str, url: str):
        """Log start of a scan operation"""
        self.info(f"Starting scan", client=client, url=url)
    
    def scan_result(self, client: str, url: str, status: str, vendor: str, config: str, details: str):
        """Log scan result"""
        self.info(
            f"Scan complete",
            client=client,
            url=url,
            status=status,
            vendor=vendor,
            config=config,
            details=details
        )
    
    def scan_error(self, client: str, url: str, error: Exception):
        """Log scan error"""
        self.error(
            f"Scan failed",
            exception=error,
            client=client,
            url=url
        )
    
    def user_action(self, action: str, **kwargs):
        """Log user action"""
        self.info(f"User action: {action}", **kwargs)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metric"""
        self.debug(f"Performance: {operation} took {duration:.2f}s", **kwargs)
    
    def _format_message(self, message: str, context: dict) -> str:
        """Format message with context dictionary"""
        if not context:
            return message
        
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        return f"{message} | {context_str}"

# ============================================================================
# LOGGER FACTORY
# ============================================================================

_loggers = {}

def get_logger(name: str) -> AppLogger:
    """
    Get or create a logger instance
    
    Args:
        name: Logger name (typically __name__ of calling module)
    
    Returns:
        AppLogger instance
    """
    if name not in _loggers:
        _loggers[name] = AppLogger(name)
    return _loggers[name]

# ============================================================================
# EXCEPTION HANDLER
# ============================================================================

def log_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Handler for unhandled exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow keyboard interrupts to propagate
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = get_logger("UncaughtException")
    logger.critical(
        "Uncaught exception",
        exception=exc_value
    )

def install_exception_handler():
    """Install the global exception handler"""
    sys.excepthook = log_unhandled_exception

# ============================================================================
# LOG VIEWER HELPERS
# ============================================================================

def get_recent_logs(max_lines: int = 100, level: Optional[str] = None) -> list:
    """
    Get recent log entries
    
    Args:
        max_lines: Maximum number of lines to return
        level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        List of log lines
    """
    log_file = LOGS_DIR / 'mom.log'
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filter by level if specified
        if level:
            lines = [l for l in lines if f" - {level} - " in l]
        
        # Return most recent lines
        return lines[-max_lines:]
    except Exception as e:
        return [f"Error reading log file: {e}"]

def get_error_logs(max_lines: int = 50) -> list:
    """Get recent error logs"""
    return get_recent_logs(max_lines, "ERROR") + get_recent_logs(max_lines, "CRITICAL")

def clear_old_logs(days: int = 30):
    """
    Clear log files older than specified days
    
    Args:
        days: Age threshold in days
    """
    try:
        cutoff = datetime.now().timestamp() - (days * 86400)
        for log_file in LOGS_DIR.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                logging.info(f"Deleted old log file: {log_file}")
    except Exception as e:
        logging.error(f"Error clearing old logs: {e}")

# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class LogExecutionTime:
    """Context manager to log execution time of a code block"""
    
    def __init__(self, logger: AppLogger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting: {self.operation}", **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.performance(self.operation, duration, **self.context)
        else:
            self.logger.error(
                f"Failed: {self.operation}",
                exception=exc_val,
                duration=duration,
                **self.context
            )
        
        # Don't suppress exceptions
        return False

# ============================================================================
# INITIALIZATION
# ============================================================================

# Setup logging when module is imported
setup_logging()
install_exception_handler()

# Create module-level logger
logger = get_logger(__name__)
logger.info("Logging system initialized")
