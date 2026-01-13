from __future__ import annotations

import json
import logging
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SETTINGS_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR


class FlooSettings:
    """
    Generic JSON settings store for FlooCast.

    - Arbitrary key/value storage (use any string as the key)
    - Persisted to ~/.config/FlooCast/ (XDG_CONFIG_HOME)
    - Includes helpers for saving/loading dict-based device info
    """

    def __init__(self, app_name: str = "FlooCast", filename: str = "settings.json"):
        self.app_name = app_name
        self.filename = filename
        self.path: Path = self._default_settings_path(app_name, filename)
        self._data: dict[str, Any] = {}
        self.load()

    # ---------- Core I/O ----------

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(self._data, dict):
                    self._data = {}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load settings from %s: %s", self.path, e)
                self._data = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self.path)
            os.chmod(self.path, SETTINGS_FILE_MODE)
        except OSError as e:
            logger.exception("Failed to save settings to %s: %s", self.path, e)
            try:
                os.remove(tmp_path)
            except OSError as cleanup_err:
                logger.warning("Failed to remove temp file %s: %s", tmp_path, cleanup_err)
            raise

    # ---------- Generic get/set ----------

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, mapping: dict[str, Any]) -> None:
        self._data.update(mapping)

    def remove(self, key: str) -> None:
        self._data.pop(key, None)

    # ---------- Named helpers for dict-based items ----------

    def set_item(self, name, item):
        if isinstance(item, dict):
            # shallow copy so the caller can't mutate stored dicts
            self._data[name] = dict(item)
        else:
            # store scalars (bool, int, str, list, etc.) directly
            self._data[name] = item

    def get_item(self, name, default=None):
        value = self._data.get(name, default)
        if isinstance(value, dict):
            # return a copy so caller can’t mutate our stored copy
            return dict(value)
        return value

    # ---------- Path helper ----------

    @staticmethod
    def _default_settings_path(app_name: str, filename: str) -> Path:
        cfg = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        return Path(cfg) / app_name / filename
