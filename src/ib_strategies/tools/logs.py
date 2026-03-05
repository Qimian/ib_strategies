import os
import logging
import random
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


# setting for log
log_file_keep_days = {
    "test": 1,
    }
log_file_keep_days_default = 1

print_console = True

logging.basicConfig(level=logging.DEBUG)

# some variables
    # default log dir
log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname( # /ib_trading
                os.path.abspath(__file__))))), "logs")
if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # loggers dict
_loggers = {}
    # log level map
level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }


# log functions
def reset_log_dir(path: str):
    """reset log dir

    Args:
        path: New log directory path
    """
    global log_dir

    log_dir = path

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

def reset_log_level(level: str):
    """reset log level"""
    logging.basicConfig(level=level_map.get(level.upper()))

def reset_print_console(print_console_: bool):
    """reset print console"""
    global print_console
    print_console = print_console_


def _get_logger(category: str) -> logging.Logger:
    """
    Get or create logger for a specific category

    Args:
        category: Log category

    Returns:
        logging.Logger instance
    """
    global _loggers

    # Return cached logger if exists
    if category in _loggers:
        return _loggers[category]

    # Create new logger
    logger = logging.getLogger(f"ib_trading.{category}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent propagation to root logger

    # Create file handler with time-based rotation
    log_file = os.path.join(log_dir, f"{category}.log")
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',  # Rotate at midnight
        interval=1,       # Every day
        backupCount=log_file_keep_days.get(
            category, log_file_keep_days_default),  # Keep last N days
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.suffix = ".%Y-%m-%d"  # Date format for rotated files

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s\t%(levelname)s\t%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Add file handler to logger
    logger.addHandler(file_handler)

    # Cache logger
    _loggers[category] = logger

    return logger


def log(category, level: str, msg: str, print_console_=None):
    """
    Log message to file and optionally print to console

    Args:
        category: Log category (str or list)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        msg: Log message
        print_console: Whether to print to console
    """

    global print_console

    if print_console_ is not None:
        print_console = print_console_

    log_level = level_map.get(level.upper())

    categories = [category] if isinstance(category, str) else category

    for cat in categories:
        _get_logger(cat).log(log_level, msg)

    if print_console_:
        print(f"{datetime.now()}\t{level.upper()}\t{'|'.join((categories))}\t{msg}")


def log_decorator(category, log_args: bool = True, log_result: bool = True):
    """
    Decorator to log function execution with parameters and return value

    Args:
        category: Log category (str or list). If list, logs to multiple files
        log_args: Whether to log function arguments (default: True)
        log_result: Whether to log function result (default: True)

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate 5-digit random id
            log_id = f"{random.randint(0, 99999):05d}"
            log_prefix = f"{func.__name__}\tfc_id:{log_id}\t"

            # Log function entry with arguments
            if log_args:
                args_str = ", ".join([str(arg) for arg in args])
                kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                params_str = ", ".join(filter(None, [args_str, kwargs_str]))
                log(category, "INFO", f"{log_prefix}called with args: [{params_str}]")

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Log return value
                if log_result:
                    result_str = str(result)[:200]  # Limit to 200 chars
                    if len(str(result)) > 200:
                        result_str += "..."
                    log(category, "INFO", f"{log_prefix}returned: {result_str}")
                else:
                    log(category, "INFO", f"{log_prefix}done, no return")

                return result

            except Exception as e:
                # Log error and re-raise
                log(category, "ERROR", f"{log_prefix}failed: {str(e)}")
                raise

        return wrapper
    return decorator

