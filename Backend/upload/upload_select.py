import os

from colorama import Back, Fore, Style

from scrapers.scrape_lublineu import upload_lublineu
from scrapers.scrape_zoom import upload_zoom
from scrapers.scrape_zoom_running import upload_zoom_running
from upload.upload_merge import upload_merge
from utils.config import COLLECTIONS
from utils.logmanager import *


def dummy():
    # only for usage with the dummy things that arent yet finished
    ...


def upload_select():
    print(f"\n{Fore.LIGHTMAGENTA_EX}Uploading menu{Style.RESET_ALL}:")
    print(
        f"{Fore.LIGHTMAGENTA_EX}1{Style.RESET_ALL} - upload files to merged collection"
    )
    print(f"{Fore.LIGHTMAGENTA_EX}2{Style.RESET_ALL} - upload to per site collections")
    answ = input(f"{Fore.LIGHTMAGENTA_EX}Select action: {Style.RESET_ALL}")
    if answ == "1":
        upload_merge()
    elif answ == "2":
        upload_individual()


def upload_individual():
    sources = {
        "lublin_eu_cykliczne.json": dummy,
        "lublin_eu_data.json": upload_lublineu,
        "zoom_events.json": upload_zoom,
        "zoom_events_running.json": upload_zoom_running,
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
