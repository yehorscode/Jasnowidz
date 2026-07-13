from colorama import Fore, Back, Style
import time
import logging
logging.basicConfig(
    level=logging.INFO,  # Set the minimum severity level to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="scraper.log",  # Optional: Save logs to a file
    filemode="w",  # Optional: 'w' to overwrite the file on each run, 'a' to append
)

def get_date():
    return time.strftime("%H:%M:%S")


def error(msg):
    logging.error(msg)
    print(
        f"{Back.RED}{get_date()} ERROR:{Style.RESET_ALL} {Fore.RED}{msg}{Style.RESET_ALL}"
    )


def warn(msg):
    logging.warning(msg)
    print(
        f"{Back.LIGHTYELLOW_EX}{get_date()} WARNING:{Style.RESET_ALL} {Fore.YELLOW}{msg}{Style.RESET_ALL}"
    )


def success(msg):
    logging.info(msg)
    print(
        f"{Back.GREEN}{get_date()} Success:{Style.RESET_ALL} {Fore.GREEN}{msg}{Style.RESET_ALL}"
    )

def info(msg):
    logging.info(msg)
    print(
        f"{Back.BLUE}{get_date()} INFO:{Style.RESET_ALL} {Fore.BLUE}{msg}{Style.RESET_ALL}"
    )

def user_input(prompt, color=Fore.WHITE, background=Back.RESET):
    logging.info("Input: " + prompt)
    user_input = input(f"{background}{color}{prompt}{Style.RESET_ALL} ")
    logging.info("Response: " + user_input)
    return user_input

