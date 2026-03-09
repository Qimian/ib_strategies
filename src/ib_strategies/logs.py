import os
import logging
import random
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


IB_LOGS_PATH = os.path.join(
    os.getcwd().replace("\\", "/").replace("\\\\", "/").split("ib_output/ib_logs")[0],
    "ib_output/ib_logs")


level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }


class MyLog:
    """Custom logger class with configurable settings"""

    def __init__(self, 
                 category: str, 
                 log_dir: str = None, 
                 keep_days: int = 7, 
                 level: str = 'DEBUG'):
        """
        Initialize logger

        Args:
            category: Log category
            log_dir: Log directory path (if not specified, use global log_dir)
            keep_days: Number of days to keep log files
            print_console: Whether to print to console
        """
        self.category = category

        if log_dir is None:
            self.log_dir = os.path.join(IB_LOGS_PATH, category)
        else:
            self.log_dir = log_dir

        if self.log_dir and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        self.logger = logging.getLogger(category)
        self.logger.setLevel(level_map[level])
        self.logger.propagate = False


        file_handler = TimedRotatingFileHandler(
            os.path.join(self.log_dir, f"{category}.log"),
            when='midnight',        # Rotate at midnight
            interval=1,             # Every day
            backupCount=keep_days,  # Keep last N days
            encoding='utf-8'
        )
        file_handler.setLevel(level_map[level])
        file_handler.suffix = ".%Y-%m-%d"  
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s\t%(levelname)s\t%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'))
        
        self.logger.addHandler(file_handler)

    def log(self, level: str, msg: str, tag = None, print_console_: bool = False):
        """
        Log message with specified level

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            msg: Log message
            print_console_: Whether to print to console (if not specified, use instance setting)
        """
        tag = "" if tag is None else f"{tag}\t"
  
        if print_console_:
            print(f"{datetime.now()}\t{level.upper()}\t{self.category}\t{tag}{msg}")

        self.logger.log(level_map[level], tag+msg)



    @staticmethod
    def log_decorator(log_args: bool = True, log_result: bool = True, tag: str = None):
        """
        Decorator to log function execution with parameters and return value

        Args:
            log_args: Whether to log function arguments (default: True)
            log_result: Whether to log function result (default: True)
            tag: Optional static tag string. If not provided, will try to use args[0].log_id

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):

                self = args[0]

                # Generate 5-digit random id
                log_id = f"{random.randint(0, 99999):05d}"
                log_prefix = f"{func.__name__}\tfc_id:{log_id}\t"

                # Determine tag: use provided tag, or try to get log_id from self (args[0])
                nonlocal tag
                if tag is None and hasattr(self, 'log_id'):
                    tag = self.log_id

                # Log function entry with arguments
                if log_args:
                    args_str = ", ".join([str(arg) for arg in args])
                    kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
                    params_str = ", ".join(filter(None, [args_str, kwargs_str]))
                    self.logger.log("INFO", f"{log_prefix}called with args: [{params_str}]", tag=tag)

                try:
                    # Execute function
                    result = func(*args, **kwargs)

                    # Log return value
                    if log_result:
                        result_str = str(result)[:200]  # Limit to 200 chars
                        if len(str(result)) > 200:
                            result_str += "..."
                        self.logger.log("INFO", f"{log_prefix}returned: {result_str}", tag=tag)
                    else:
                        self.logger.log("INFO", f"{log_prefix}done, no return", tag=tag)

                    return result

                except Exception as e:
                    # Log error and re-raise
                    self.logger.log("ERROR", f"{log_prefix}failed: {str(e)}", tag=tag)
                    raise

            return wrapper
        return decorator






