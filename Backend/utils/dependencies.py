from utils.logmanager import error, warn, success, info, user_input
import os


def checkDependency():
    hasRequests = None
    hasSoup = None
    hasAppwrite = None
    hasColorama = None
    hasTQDM = None
    try:
        import tqdm

        hasTQDM = True
    except ImportError:
        hasTQDM = False
        error("tqdm missing")
    try:
        import colorama

        hasColorama = True
    except ImportError:
        hasColorama = False
        error("colorama missing")
    try:
        import requests

        hasRequests = True
    except ImportError:
        hasRequests = False
        error("requests missing")

    try:
        from bs4 import BeautifulSoup

        hasSoup = True
    except ImportError:
        hasSoup = False
        error("bs4 missing")

    if hasRequests and hasSoup and hasColorama and hasTQDM:
        info("All dependencies installed")
    else:
        error("Install all needed dependencies")
    return hasRequests, hasSoup, hasColorama, hasTQDM
