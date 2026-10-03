from datetime import datetime

from bs4 import BeautifulSoup
from openrouter import OpenRouter
import requests

from scrapers.scrape_labirynt import parse_event_duration, scrape_event
from utils.config import get_ratelimit_count, increment_ratelimit, load_env
from utils.headers import headers

AI_MODEL = "deepseek/deepseek-v4-flash"
AI_URL = "https://ai.hackclub.com/proxy/v1"
string = """

							02-9-2026 - 03-9-2026
						"""
# print(string.strip())
# print(parse_event_duration(string.strip(), router=router))

env = load_env()
# router = OpenRouter(api_key=env.get("HCAI_KEY"), server_url=AI_URL)

# response = requests.get("https://labirynt.com/wystawy", headers=headers)

url = "https://labirynt.com/wydarzenia"
base_url = "https://labirynt.com"

# response = requests.get(url, headers=headers)

# content = response.content
# soup = BeautifulSoup(content, "html.parser")
# data = []
# events = soup.find_all("div", class_="futureEvent")

# print(events)
#
#
print(f"cur {get_ratelimit_count()}")
increment_ratelimit()
print(f"cur {get_ratelimit_count()}")

print(datetime.now())
