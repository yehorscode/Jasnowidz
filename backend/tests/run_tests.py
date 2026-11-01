from colorama import Fore, Style

from tests.test_logging import test_logging
from tests.test_pocketbase import test_pocketbase
from tests.test_proxy import test_proxy


def run_tests():
    print(f"{Fore.LIGHTMAGENTA_EX}\nModule tests{Style.RESET_ALL}")

    print(f"{Fore.LIGHTMAGENTA_EX} p{Style.RESET_ALL} - pocketbase tests")
    print(f"{Fore.LIGHTMAGENTA_EX} l{Style.RESET_ALL} - test logging")
    print(f"{Fore.LIGHTMAGENTA_EX} 2{Style.RESET_ALL} - test proxy availability")

    action = input(f"{Fore.LIGHTMAGENTA_EX}\nSelect action: {Style.RESET_ALL}")
    action = action.lower()
    if action == "p":
        test_pocketbase()
    elif action == "l":
        test_logging()
    elif action == "2":
        test_proxy()
