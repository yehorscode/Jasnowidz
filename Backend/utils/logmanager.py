import logging
import time
from venv import logger

from colorama import Back, Fore, Style

logging.basicConfig(
    level=logging.INFO,  # Set the minimum severity level to log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="scraper.log",  # Optional: Save logs to a file
    filemode="w",  # Optional: 'w' to overwrite the file on each run, 'a' to append
)


def get_date():
    return time.strftime("%H:%M:%S")


def error(msg):
    logger.error(msg)
    print(
        f"{Back.RED}{get_date()} ERROR:{Style.RESET_ALL} {Fore.RED}{msg}{Style.RESET_ALL}"
    )


def warn(msg):
    logger.warning(msg)
    print(
        f"{Back.LIGHTYELLOW_EX}{get_date()} WARNING:{Style.RESET_ALL} {Fore.YELLOW}{msg}{Style.RESET_ALL}"
    )


def success(msg):
    logger.info(msg)
    print(
        f"{Back.GREEN}{get_date()} Success:{Style.RESET_ALL} {Fore.GREEN}{msg}{Style.RESET_ALL}"
    )


def info(msg):
    logger.info(msg)
    print(
        f"{Back.BLUE}{get_date()} INFO:{Style.RESET_ALL} {Fore.BLUE}{msg}{Style.RESET_ALL}"
    )


def user_input(prompt, color=Fore.WHITE, background=Back.RESET):
    logger.info("Input: " + prompt)
    user_input = input(f"{background}{color}{prompt}{Style.RESET_ALL} ")
    logger.info("Response: " + user_input)
    return user_input
