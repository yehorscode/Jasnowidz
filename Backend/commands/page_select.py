from colorama import Back, Style

from scrapers.scrape_lublineu import scrape_lublineu
from scrapers.scrape_zoom import scrape_zoom
from scrapers.scrape_zoom_running import scrape_zoom_running
from utils.logmanager import *


def select_scrape_site():
    print(f"{Fore.GREEN}Select what to scrape:{Style.RESET_ALL}")
    print(f"{Fore.RED} 1 {Style.RESET_ALL} - All (Long)")
    print(
        f"{Fore.CYAN} 2 {Style.RESET_ALL} - https://lublin.eu/kultura/wydarzenia/ (events + running)"
    )
    print(f"{Fore.CYAN} 3 {Style.RESET_ALL} - https://zoom.lublin.pl (events)")
    print(
        f"{Fore.CYAN} 4 {Style.RESET_ALL} - https://zoom.lublin.pl/w-trakcie (running events)"
    )
    info("Remember: do not run the script too often or you will be ratelimited")
    response = user_input("Select: ")
    if response == "1":
        scrape_lublineu()
        scrape_zoom()
        scrape_zoom_running()
        success("\a \n SCRAPING ENDED")
    if response == "2":
        scrape_lublineu()
    if response == "3":
        scrape_zoom()
    if response == "4":
        scrape_zoom_running()
