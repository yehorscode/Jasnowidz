from commands.auth import handle_login
from utils.dependencies import checkDependency
from utils.logmanager import get_date, error, warn, success, info, user_input
import os
from colorama import Fore, Back, Style
from commands.wybierz_strone import wybierzStrone
from utils.checkstatus import checkStatus
from utils.mergeandsend import mergeandsend
from commands.mergedata import mergedata
from tests.run_tests import run_tests
def chooseAction():
    print(f"{Fore.GREEN}Main app menu{Style.RESET_ALL}:")
    print(f"{Fore.GREEN} 1 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 2 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 3 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 4 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 5 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} 6 {Style.RESET_ALL}- ")
    print(f"{Fore.GREEN} t {Style.RESET_ALL}- modules testing")
    print(f"{Fore.GREEN} a {Style.RESET_ALL}- auth")
    action = input(f"{Fore.GREEN}\nSelect action:{Style.RESET_ALL}")

    if action == "t":
        run_tests()
    elif action == "a":
        handle_login()

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

start()
