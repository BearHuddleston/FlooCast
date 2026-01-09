#!/usr/bin/env python3
"""Entry point for floocast application."""

import os
import sys


def main():
    if getattr(sys, "frozen", False):
        app_dir = os.path.dirname(sys.executable)
    elif os.path.exists("/opt/floocast/FlooCastApp.ico"):
        app_dir = "/opt/floocast"
    else:
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    os.chdir(app_dir)
    sys.argv[0] = os.path.join(app_dir, "main.py")

    from floocast import app  # noqa: F401


if __name__ == "__main__":
    main()
