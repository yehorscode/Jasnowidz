from utils.connecter import get_proxy, pget
from utils.headers import headers
from utils.logmanager import error, info, success, warn


def test_proxy():
    info("Testing the proxy availability")
    proxies = get_proxy()
    if proxies == None:
        choice = input(warn("No proxies are set! Continue anyways? (Y/n)"))
        if choice == "" or choice.lower() == "y" or choice.lower() == "yes":
            info("Continuing")
        else:
            info("Stopping")
            return
    else:
        info(f"Proxies set: [{proxies}]")
    response = pget("https://www.quad9.net", headers=headers)
    if response.status_code == 200:
        success("Everything is probably working alright")
    else:
        error(
            f"There has been some error and it's error code is {response.status_code}"
        )
