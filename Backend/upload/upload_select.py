import os

from colorama import Back, Fore, Style

from strony.scrape_lublineu import upload_lublineu
from strony.scrape_zoom import upload_zoom
from utils.config import COLLECTIONS
from utils.logmanager import *


def dummy():
    # onlt for usage with the dummy things that arent yet finished
    ...


def upload_select():
    print(f"\n{Fore.LIGHTMAGENTA_EX}Select what to upload{Style.RESET_ALL}:")
    sources = {
        "lublin_eu_cykliczne.json": dummy,
        "lublin_eu_data.json": upload_lublineu,
        "zoom_events.json": upload_zoom,
    }
    files = os.listdir("./data")
    info(f"Found these files {files}")
    to_run = []
    for filename, func in sources.items():
        if filename in files:
            info(f"Running {func.__name__}")
            to_run.append(func)

    if not to_run:
        warn("No files to upload")
        return

    to_run_items = ",".join(fn.__name__ for fn in to_run)
    print(f"\n{Fore.LIGHTMAGENTA_EX}About to upload {to_run_items}{Style.RESET_ALL}")
    confirmation = input(
        f"{Back.LIGHTMAGENTA_EX}Confirm or deny? (Y/n):{Style.RESET_ALL} "
    )
    confirmation = confirmation.lower()

    if confirmation == "y" or confirmation == "":
        info("Okay")
        for func in to_run:
            info(f"Running {func.__name__}")
            func()
    else:
        info("Cancelled")
