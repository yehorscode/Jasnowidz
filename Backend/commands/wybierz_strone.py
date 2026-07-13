from colorama import Fore, Back, Style
from utils.logmanager import get_date, error, warn, success, info, user_input
from strony.scrape_lublineu import scrape_lublineu
from strony.scrape_zoom import scrape_zoom
from strony.scrape_zoom_cykliczne import scrape_zoom_cykliczne

def wybierzStrone():
    print(f"{Back.GREEN}Wybierz metodę scrapowania:{Style.RESET_ALL}")
    print(f"{Back.RED} 1 {Style.RESET_ALL} - Wszystko (Długo)")
    print(f"{Back.LIGHTYELLOW_EX} 2 {Style.RESET_ALL} - https://lublin.eu/kultura/wydarzenia/")
    print(f"{Back.LIGHTYELLOW_EX} 3 {Style.RESET_ALL} - https://zoom.lublin.pl (wydarzenia)")
    print(f"{Back.LIGHTYELLOW_EX} 4 {Style.RESET_ALL} - https://zoom.lublin.pl/w-trakcie (trwające)")
    info(
        "Pamiętaj: Nie włączaj zbyt często albo cię zablokują! Scrapowanie może być długie lub nieść odpowiedzialność prawną!"
    )
    response = user_input("Wybierz: ")
    if response == "1":
        info("Wybrano 1")
        print()
        scrape_lublineu()
        scrape_zoom()
        scrape_zoom_cykliczne()
        print()
        print()
        success("ZAKOŃCZONO SCRAPOWANIE")
    if response == "2":
        info("Wybrano 2")
        print()
        scrape_lublineu()
    if response == "3":
        info("Wybrano 3")
        print()
        scrape_zoom()
    if response == "4":
        info("Wybrano 4")
        print()
        scrape_zoom_cykliczne()
