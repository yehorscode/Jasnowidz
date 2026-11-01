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
    from colorama import Fore, Style

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


class NoSourceError(Exception):
    """No source for the input provided"""


def makedate(date: str, time="", source="") -> str | tuple[str, str] | list[str]:
    if source == "labirynt_event":
        if " - " in date:
            dt1, dt2 = date.split(" - ")
            dt1 = datetime.strptime(dt1.strip(), "%d-%m-%Y").isoformat()
            dt2 = datetime.strptime(dt2.strip(), "%d-%m-%Y").isoformat()
            return dt1, dt2  # start_date, end_date
        else:
            return datetime.strptime(date, "%d-%m-%Y").isoformat()  # start date
    elif source == "labirynt_exhibition":
        dt1 = date[:10]  # the part before -
        dt2 = date[13:]  # the part after -
        dt1 = datetime.strptime(dt1, "%d-%m-%Y").isoformat()
        dt2 = datetime.strptime(dt2, "%d-%m-%Y").isoformat()
        return dt1, dt2  # start_date, end_date
    elif source == "lublineu_event":
        if time:
            dt = f"{date} {time}"
            return datetime.strptime(dt, "%d-%m-%Y %H:%M").isoformat()
        else:
            dt = date
            return datetime.strptime(dt, "%d-%m-%Y").isoformat()
    elif source == "lublineu_running":
        dt = date
        return datetime.strptime(dt, "%Y-%m-%d").isoformat()
    elif source == "zoom_running":
        dt1 = date[:10]  # before -
        dt2 = date[13:]  # after -
        dt1 = datetime.strptime(dt1, "%Y-%m-%d").isoformat()
        dt2 = datetime.strptime(dt2, "%Y-%m-%d").isoformat()
        return dt1, dt2
    elif source == "zoom_event":
        if ":" in date:
            dtt = date[13:]  # after -, if there is time
            dt1 = date[:10]  # before -, the date
            if "," in dtt:
                dtt = dtt.split(",")
                return [
                    datetime.strptime(
                        f"{dt1} {tm.strip()}", "%Y-%m-%d %H:%M"
                    ).isoformat()
                    for tm in dtt
                ]
            dtc = f"{dt1} {dtt}"
            return datetime.strptime(dtc, "%Y-%m-%d %H:%M").isoformat()
        else:
            dt1 = date[:10]  # before -
            dt2 = date[13:]  # after -
            dt1 = datetime.strptime(dt1, "%Y-%m-%d").isoformat()
            dt2 = datetime.strptime(dt2, "%Y-%m-%d").isoformat()
            return dt1, dt2
    else:
        raise NoSourceError
