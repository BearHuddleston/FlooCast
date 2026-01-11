# FlooCast Development Notes

## Project Overview

FlooCast is a Python GUI application for controlling FlooGoo Bluetooth USB dongles (FMA120). Uses wxPython for the GUI, serial communication for the protocol, and sounddevice for audio routing.

## Development Setup

- **Python**: 3.10+ required
- **Package manager**: uv (lockfile at `uv.lock`)
- **wxPython (GUI)**: Optional dependency, requires GTK3 dev files on Linux:
  ```bash
  sudo apt install libgtk-3-dev libwebkit2gtk-4.1-dev libsdl2-dev
  uv sync --extra gui
  ```
- **Dev dependencies**: `uv sync --extra dev`

## Code Quality

- Always run `uv run pre-commit run --all-files` before committing
- mypy is enforced in pre-commit; type annotations required
- Dynamic attributes (via `setattr` with `VALUE_ATTR` pattern) need explicit type annotations on the class

## Architecture

- `src/floocast/protocol/` - Serial protocol messages and state machine
- `src/floocast/gui/` - wxPython GUI panels and components
- `src/floocast/audio/` - Audio routing via sounddevice
- `src/floocast/app.py` - Main application entry point

## CI Notes

- wxPython is optional (`[gui]` extra) to avoid GTK build in CI
- CI runs: ruff, mypy, pytest
- Pre-push hook mirrors CI checks locally
