import logging
import os

# ANSI escape codes for colors
BRIGHT_RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
GREEN = '\033[92m'
RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter with enhanced color support"""

    COLORS = {
        'DEBUG': CYAN,
        'INFO': GREEN,
        'WARNING': YELLOW,
        'ERROR': BRIGHT_RED,
        'CRITICAL': BRIGHT_RED
    }

    def format(self, record):
        # Color the entire error and critical messages
        if record.levelname in ['ERROR', 'CRITICAL']:
            record.msg = f"{self.COLORS[record.levelname]}{record.msg}{RESET}"

        # Add color to level names for all levels
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{RESET}"

        return super().format(record)

def setup_logging():
    """Configure logging with enhanced colored output"""
    # Create formatter with improved format
    formatter = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Remove existing handlers to avoid duplicate logs
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Configure file handler for bot.log
    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(file_handler)

    # Set specific levels for some loggers
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('wavelink').setLevel(logging.INFO)

    # Add custom log levels colors
    logging.addLevelName(logging.ERROR, f"{BRIGHT_RED}ERROR{RESET}")
    logging.addLevelName(logging.CRITICAL, f"{BRIGHT_RED}CRITICAL{RESET}")