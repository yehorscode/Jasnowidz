import json
import os

from colorama import Back, Fore, Style


def print_stats():
    print()
    path = "./data/"
    dir = os.listdir(path)
    if not dir:
        print("No files found in data/. Run a scrape to get some data first")
        return
    total = 0
    for file in dir:
        if file.endswith("json"):
            with open(path+file, "r") as f:
                data = json.loads(f.read())
                print(f"{Fore.CYAN}{file} - {len(data)} entries{Style.RESET_ALL}")
                total += len(data)
    print(f"{Fore.GREEN}Total {total} entries in all data files{Style.RESET_ALL}")
