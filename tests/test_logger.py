import logging
import sys

from src.services.logger import setup_logger  # поправь путь импорта


def test_setup_logger_returns_logger():
    logger = setup_logger("test_logger")

    assert isinstance(logger, logging.Logger)


def test_logger_name_is_correct():
    logger = setup_logger("my_logger")

    assert logger.name == "my_logger"


def test_logger_level_is_info():
    logger = setup_logger("level_test")

    assert logger.level == logging.INFO


def test_logger_has_stream_handler():
    logger = setup_logger("handler_test")

    handlers = logger.handlers
    stream_handlers = [
        h for h in handlers if isinstance(h, logging.StreamHandler)
    ]

    assert len(stream_handlers) == 1
    assert stream_handlers[0].stream is sys.stdout


def test_logger_formatter_is_correct():
    logger = setup_logger("formatter_test")

    handler = logger.handlers[0]
    formatter = handler.formatter

    assert formatter is not None
    assert formatter._fmt == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"


def test_logger_does_not_duplicate_handlers():
    logger = setup_logger("no_duplicate")

    handlers_before = len(logger.handlers)
    setup_logger("no_duplicate")
    handlers_after = len(logger.handlers)

    assert handlers_before == handlers_after
