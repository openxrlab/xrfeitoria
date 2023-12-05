import logging


class UniqueFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.unique_messages = set()

    def filter(self, record):
        # Extract the log message from the record
        log_message = record.getMessage()

        # Check if the message is unique
        if log_message not in self.unique_messages:
            self.unique_messages.add(log_message)
            return True
        else:
            return False


def setup_logger(level: str = 'INFO') -> 'logging.Logger':
    """Setup logging to file and console.

    Args:
        level (str, optional): logging level. Defaults to "INFO", can be "DEBUG", "INFO", "WARNING",
                                "ERROR", "CRITICAL".
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.handlers.clear()
    logger.setLevel(level)
    logger_format = '{asctime} | ' + '{levelname:^8} | ' + '[blender] {message}'
    formatter = logging.Formatter(logger_format, style='{', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addFilter(UniqueFilter())
    return logger


logger = setup_logger()
