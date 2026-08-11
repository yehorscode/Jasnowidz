# config.py
POCKETBASE_URL = "https://jasnowidzdb.yehor.pl.eu.org"

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
