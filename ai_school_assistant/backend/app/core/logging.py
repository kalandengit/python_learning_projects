"""Structured logging setup.

JSON-ish key=value structured logs so lines are grep-able in dev and parseable
by the log pipeline in deployed environments. Swapped for OTel-integrated
logging when observability lands (Milestone 2).
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="ts=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]
