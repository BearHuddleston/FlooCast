#!/usr/bin/env python3
"""Entry point for floocast application."""

import logging
import os
import sys


def _configure_logging():
    level_name = os.environ.get("FLOOCAST_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    _configure_logging()

    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
    elif os.path.exists("/opt/floocast/locales"):
        app_dir = "/opt/floocast"
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    os.chdir(app_dir)
    sys.argv[0] = os.path.join(app_dir, "main.py")

    from floocast import app  # noqa: F401


if __name__ == "__main__":
    main()
