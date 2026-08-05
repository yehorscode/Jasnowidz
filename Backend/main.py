import os
import sys

from colorama import Back, Fore, Style

from commands.auth import handle_login
from commands.wybierz_strone import selectScrapeSite
from tests.run_tests import run_tests
from upload.upload_select import upload_select
from utils.dependencies import checkDependency
from utils.logmanager import error, info, success, warn

# from utils.mergeandsend import mergeandsend


def chooseAction():
    print(f"{Fore.GREEN}Main app menu{Style.RESET_ALL}:")
    print(f"{Fore.GREEN} 1 {Style.RESET_ALL}- scrape select")
    print(f"{Fore.GREEN} 2 {Style.RESET_ALL}- upload select")
    print(f"{Fore.GREEN} 3 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 4 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 5 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 6 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} t {Style.RESET_ALL}- modules testing")
    print(f"{Fore.GREEN} a {Style.RESET_ALL}- auth")
    action = input(f"{Fore.GREEN}\nSelect action: {Style.RESET_ALL}")
    action = action.lower()
    if action == "t":
        run_tests()
    elif action == "a":
        handle_login()
    elif action == "1":
        selectScrapeSite()
    elif action == "2":
        upload_select()
    else:
        warn(f"Unrecognised command {action} quitting")
        sys.exit()


def start():
    info("Run")
    checkFolders()
    checkDependency()
    info("Dependency check end\n")
    chooseAction()


def checkFolders():
    if not os.path.exists("./robots"):
        error("/robots doesn't exist")
        os.makedirs("./robots")
        success("Created /robots")
    if not os.path.exists("./data"):
        error("/data doesn't exist")
        os.makedirs("./data")
        success("Created /data")

if __name__ == "__main__":
    start()
