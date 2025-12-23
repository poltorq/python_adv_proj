import logging
import sys


def setup_logger(name: str = __name__) -> logging.Logger:
    """Настройка логгера"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Форматтер
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (опционально)
        # file_handler = logging.FileHandler('bot.log')
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger
