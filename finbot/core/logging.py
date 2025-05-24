import logging.config
from typing import Optional


def configure_logging(log_level: Optional[str] = None) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s (%(threadName)s) [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                }
            },
            "root": {"level": log_level or "INFO", "handlers": ["wsgi"]},
        }
    )
