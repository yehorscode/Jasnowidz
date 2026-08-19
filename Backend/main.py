import os
import sys

from colorama import Back, Fore, Style

from commands.auth import handle_login
from commands.delete_all import delete_all_records, delete_local_data
from commands.page_select import select_scrape_site
from tests.run_tests import run_tests
from upload.upload_select import upload_select
from utils.config import open_config
from utils.logmanager import error, info, success, warn
from utils.print_stats import print_stats

# from utils.mergeandsend import mergeandsend


def chooseAction():
    print(f"{Fore.GREEN}Main app menu{Style.RESET_ALL}:")
    print(f"{Fore.GREEN} 1 {Style.RESET_ALL}- scrape select")
    print(f"{Fore.GREEN} 2 {Style.RESET_ALL}- upload select")
    print(f"{Fore.GREEN} 3 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 4 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} c {Style.RESET_ALL}- config")
    print(f"{Fore.GREEN} t {Style.RESET_ALL}- modules testing")
    print(f"{Fore.GREEN} a {Style.RESET_ALL}- auth")
    print(f"{Fore.GREEN} d {Style.RESET_ALL}- delete all remote records")
    print(f"{Fore.GREEN} dl {Style.RESET_ALL}- delete local records")
    print(f"{Fore.GREEN} stat {Style.RESET_ALL}- print scraped data stats")
    action = input(f"{Fore.GREEN}\nSelect action: {Style.RESET_ALL}")
    action = action.lower()
    if action == "t":
        run_tests()
    elif action == "c":
        open_config()
    elif action == "a":
        handle_login()
    elif action == "d":
        delete_all_records()
    elif action == "1":
        select_scrape_site()
    elif action == "2":
        upload_select()
    elif action == "dl":
        delete_local_data()
    elif action == "stat":
        print_stats()
    else:
        warn(f"Unrecognised command {action} quitting")
        sys.exit()


def start():
    info("Run")
    checkFolders()
    info("Dependency check end\n")
    chooseAction()


def checkFolders():
    if not os.path.exists("./data"):
        error("/data doesn't exist")
        os.makedirs("./data")
        success("Created /data")


if __name__ == "__main__":
    start()
