from colorama import Fore, Style, Back

from tests.test_pocketbase import test_pocketbase

def run_tests():
    print(f"{Fore.LIGHTMAGENTA_EX}\nModule tests{Style.RESET_ALL}")

    print(f"{Fore.LIGHTMAGENTA_EX} p{Style.RESET_ALL} - pocketbase tests")

    action = input(f"{Fore.LIGHTMAGENTA_EX}\nSelect action: {Style.RESET_ALL}")

    if action == "p":
        test_pocketbase()
