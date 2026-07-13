import requests
from utils.logmanager import error, success, info, warn, user_input
from utils.headers import headers

def checkStatus(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            success(f"Strona: {url} działa: {response.status_code}")
            return True
        else:
            error(f"Strona: {url} nie działa: {response.status_code}")
            error(f"Dlaczego?: {response.reason}")
            return False
    except:
        error(f"Strona: {url} nie działa: Niewiadomy error, sprawdź zainstalowane pakiety")
        return False