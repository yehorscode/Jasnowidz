from random import randint

import requests

from utils.config import load_config
from utils.headers import headers

# only supports http:// or https:// proxies. is an array
proxy_url = load_config().get("proxy", "").get("url")


def get_proxy() -> dict | None:
    if proxy_url == None:
        return None
    rpx = proxy_url[randint(0, len(proxy_url) - 1)]
    return {"http": rpx, "https": rpx}


def pget(url: str, **kwargs):
    if get_proxy() != None:
        kwargs.setdefault("proxies", get_proxy())
        kwargs.setdefault("headers", headers)
        kwargs.setdefault("timeout", 15)
    return requests.get(url, **kwargs)
