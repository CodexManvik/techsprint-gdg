"""
Structured logging configuration using structlog.

Provides JSON logs with automatic context (session_id, user_id, timestamps).
"""
import logging
import sys

try:
    import structlog
    
    def setup_structured_logging():
        """Configure structlog for JSON output with timestamps and context."""
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
            cache_logger_on_first_use=True,
        )
        
        # Also configure stdlib logging to use structlog
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
        )
        
        return structlog.get_logger()
    
    def get_logger(name: str = None):
        """Get a structured logger instance."""
        return structlog.get_logger(name)
    
    STRUCTLOG_AVAILABLE = True

except ImportError:
    # Fallback to stdlib logging if structlog not installed
    def setup_structured_logging():
        """Fallback to stdlib logging."""
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO,
            stream=sys.stdout
        )
        logging.info("structlog not available, using stdlib logging")
        return logging.getLogger()
    
    def get_logger(name: str = None):
        """Get a stdlib logger instance."""
        return logging.getLogger(name)
    
    STRUCTLOG_AVAILABLE = False
