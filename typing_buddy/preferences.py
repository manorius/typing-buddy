import json
import os
from typing import Dict

DEFAULTS: Dict[str, int] = {
    "wpm": 120,        # Words per minute (5 chars per word)
    "countdown": 3,    # Seconds before typing starts
}

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".typing_buddy")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def load_preferences() -> Dict[str, int]:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "wpm": int(data.get("wpm", DEFAULTS["wpm"])),
                    "countdown": int(data.get("countdown", DEFAULTS["countdown"]))
                }
    except Exception:
        # Fallback to defaults on any error
        pass
    return DEFAULTS.copy()


def save_preferences(prefs: Dict[str, int]) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        # Only persist known keys
        data = {
            "wpm": int(prefs.get("wpm", DEFAULTS["wpm"])),
            "countdown": int(prefs.get("countdown", DEFAULTS["countdown"]))
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        # Silently ignore save errors; UI can still function
        pass

