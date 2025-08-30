# logging_config.py
import os
import logging
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logging(app):
    """Setup logging configuration for the Flask application"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(Config.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set log level
    log_level = getattr(logging, Config.LOG_LEVEL.upper())
    
    # Configure root logger only if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers and not root_logger.isEnabledFor(logging.INFO):
        logging.basicConfig(
            level=log_level,
            format=Config.LOG_FORMAT,
            handlers=[
                # Console handler
                logging.StreamHandler(),
                # File handler with rotation
                RotatingFileHandler(
                    Config.LOG_FILE,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
            ]
        )
    
    # Set Flask logger level
    app.logger.setLevel(log_level)
    
    # Set SQLAlchemy logger level (reduce noise in development)
    if app.debug:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Set other noisy loggers to WARNING
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Log application startup
    app.logger.info('Application logging configured')
    app.logger.info(f'Log level: {Config.LOG_LEVEL}')
    app.logger.info(f'Log file: {Config.LOG_FILE}')

def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)
