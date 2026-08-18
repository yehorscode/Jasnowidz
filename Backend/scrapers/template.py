import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from commands.auth import pocketbaseLogin
from utils import pocketbase
from utils.config import load_config
from utils.headers import headers
from utils.logmanager import error, info, success, warn

# Scraping script for x site
# id in config: script_id

MAX_WORKERS = 1


def _scrape_event(event):
    # logic for scraping a single item
    ...


def _run_parralel_scrape(event_list, max_workers=MAX_WORKERS):
    results = []
    if not event_list:
        return results
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_event = {
            executor.submit(_scrape_event, event): event for event in event_list
        }
        for future in tqdm(
            as_completed(future_to_event),
            total=len(event_list),
            desc="Scraping events...",
            unit="event",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
            colour="green",
            ascii=True,
        ):
            data = future.result()
            if data:
                results.append(data)

        return results


def _scrape_something():
    config = load_config()
    config = config["scrapers"]
    url = "https://full.event.url/something"
    base_url = "https://base.site.url"

    info(f"Starting diagnostics for: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        error(f"Error while downloading {url}: {response.status_code}")
        return
    else:
        success("Page works")

    success("Checks ended")

    info(f"Scraping page: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")
    data = []
    events = soup.find_all("div", class_="some")
    if config["site_config_entryname"]["enabled"]:
        for event in tqdm(
            events,
            desc="Searching...",
            unit="event",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
            colour="green",
            ascii=True,
        ):
            ...
    else:
        warn("Scraping site_config_entryname is disabled in config")

    # at the end of the scraping loop add how many items were scraped and save the file
    with open(f"./data/{config['script_id']['output']}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success("Saved data to JSON files.")


# add this function to the upload handler at upload_select.py > sources
def _upload_something():
    config = load_config()
    config = config["scrapers"]
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    info("Uploading scraped (running events) data from site url")
    with open(f"./data/{config['script_id']['output']}", "r") as f:
        events = json.load(f)

    for event in events:
        try:
            pocketbase.create_record(
                collection="collection_name", data=event, authorization=token
            )
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
