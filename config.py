from __future__ import annotations
import json
import os
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Gcalcal"
CONFIG_FILE = APP_DIR / "settings.json"
TOKEN_FILE = APP_DIR / "token.json"

DEFAULTS = {
    "calendar_id": "primary",
    "all_calendars": True,
    "holiday_calendar_id": "",
    "credentials_file": "",
    "opacity": 0.94,
    "always_on_top": True,
    "frameless": True,
    "window_x": 80,
    "window_y": 80,
    "window_width": 440,
    "window_height": 600,
    "accent_color": "#72D6B4",
    "background_image": "",
    "show_agenda": True,
    "refresh_minutes": 15,
}


def load_config() -> dict:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    data = DEFAULTS.copy()
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict):
            data.update(loaded)
    except (OSError, json.JSONDecodeError):
        pass
    return data


def save_config(data: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(CONFIG_FILE)
