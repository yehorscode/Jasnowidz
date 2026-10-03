import json
import threading
import time
from datetime import datetime

from utils.logmanager import warn

_ratelimit_lock = threading.Lock()
# config.py
POCKETBASE_URL = "https://jasnowidzdb.yehor.pl.eu.org"
AI_URL = "https://ai.hackclub.com/proxy/v1"
COLLECTIONS = [
    "test",
    "lubeu_events",
    "zoom_running",
    "lubeu_running",
    "zoom",
    "labirynt",
    "labirynt_wydarzenia",
]


def open_config():
    from colorama import Back, Fore, Style

    print(f"{Fore.GREEN}\nConfig menu:{Style.RESET_ALL}")
    print(
        f"Colors: {Fore.CYAN}Changeable{Style.RESET_ALL} | {Fore.RED}Unchangable{Style.RESET_ALL}"
    )

    print(f"{Fore.RED}{POCKETBASE_URL}{Style.RESET_ALL}")


import tomllib
from pathlib import Path

from utils.logmanager import error

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.toml"
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        error(f"Config not found at: {CONFIG_PATH}")
        return {}

    try:
        with open(CONFIG_PATH, "rb") as conf:
            return tomllib.load(conf)
    except tomllib.TOMLDecodeError as e:
        error(f"Failed to load config: {e}")
        return {}
    except OSError as e:
        error(f"Failed to read config: {e}")
        return {}


def load_env():
    import os

    from dotenv import load_dotenv

    env_path = BASE_DIR / ".env"
    if not env_path.is_file():
        error(f".env file not found at: {env_path}")
        return {}

    load_dotenv(dotenv_path=env_path)
    return dict(os.environ)


def load_cache(file: str):
    import json

    cache_path = CACHE_DIR / file
    if not cache_path.is_file():
        return None
    with open(cache_path, "r") as f:
        dat = json.load(f)
        f.close()
        return dat


def save_cache(data, file: str):
    import json

    cache_path = CACHE_DIR / file
    with open(cache_path, "w") as f:
        json.dump(data, f, indent=4)
        f.close()


def increment_ratelimit():
    """
    Adds 1 to the ratelimit count saved in cache. When it hits 750 it
    stops any scraping (by blocking the caller) and waits 32 minutes.
    """
    with _ratelimit_lock:
        now_count = get_ratelimit_count() + 1
        cache_path = CACHE_DIR / "ratelimit.json"
        with open(cache_path, "w") as f:
            json.dump({"count": now_count, "timestamp": datetime.now().isoformat()}, f)

        if now_count >= 750:
            warn(f"Rate limit hit ({now_count}/750) — sleeping 32 minutes")
            time.sleep(32 * 60)
            reset_ratelimit()

        return now_count


def reset_ratelimit():
    """
    Resets the ratelimit count saved in cache to 0
    """
    cache_path = CACHE_DIR / "ratelimit.json"
    with open(cache_path, "w") as f:
        json.dump({"count": 0, "timestamp": datetime.now().isoformat()}, f)


def get_ratelimit_count() -> int:
    """
    Returns the ratelimit count saved in cache
    """
    cache_path = CACHE_DIR / "ratelimit.json"
    if not cache_path.is_file():
        with open(cache_path, "w") as f:
            json.dump({"count": 0, "timestamp": None}, f)
        return 0
    with open(cache_path, "r") as f:
        data = json.load(f)
    return data.get("count", 0)
