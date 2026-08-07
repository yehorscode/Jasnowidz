import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from commands.auth import pocketbaseLogin
from utils import pocketbase
from utils.config import load_config
from utils.headers import headers
from utils.logmanager import error, info, success, warn

# Scraping script for labirynt.com site
# id in config: labirynt_exhibitions


def parse_event_duration(duration_str):
    if not duration_str or " - " not in duration_str:
        return None, None

    start_raw, end_raw = [part.strip() for part in duration_str.split(" - ")]

    start_dt = datetime.strptime(start_raw, "%d-%m-%Y")
    end_dt = datetime.strptime(end_raw, "%d-%m-%Y")

    local_tz = ZoneInfo("Europe/Warsaw")
    start_aware = start_dt.replace(tzinfo=local_tz).astimezone(timezone.utc)
    end_aware = end_dt.replace(tzinfo=local_tz).astimezone(timezone.utc)

    return start_aware.isoformat(), end_aware.isoformat()


def scrape_labirynt_exhibitions():
    config = load_config()
    config = config["scrapers"]
    url = "https://labirynt.com/wystawy/"
    base_url = "https://labirynt.com"

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
    future_content = requests.get("https://labirynt.com/wystawy/?future=true")
    soup = BeautifulSoup(content, "html.parser")
    future_soup = BeautifulSoup(future_content.content, "html.parser")
    data = []
    events = soup.find_all("div", class_="futureEvent")
    future_events = future_soup.find_all("div", class_="futureEvent")

    def scrape_event(event):
        event_link = event.find("a", class_="futureEvent__img")
        event_link = event_link["href"] if event_link else None
        img_tag = event.select_one("a.futureEvent__img img")
        event_img = None
        if img_tag:
            event_img = (
                img_tag.get("data-src-webp")
                or img_tag.get("data-src-img")
                or img_tag.get("src")
            )
        event_name = event.find("h2")
        if event_name:
            event_name = event_name.find("a")
            event_name = event_name.text if event_name else None
        full_event = requests.get(str(event_link), headers=headers)
        event_bs = BeautifulSoup(full_event.content, "html.parser")

        # this is basically the description + some additional data
        event_description = event_bs.find("div", class_="wysiwyg")

        # DURATION not date!!!! DD-MM-YYYY - DD-MM-YYYY (MM without zeros)
        event_duration = event_bs.find("p", class_="postContent__dateTitle")
        event_duration = event_duration.get_text(strip=True) if event_duration else None
        start_date, end_date = parse_event_duration(event_duration)
        event_cost = None
        for box in event_bs.select("div.postContent__box"):
            title = box.select_one("p.postContent__boxTitle")
            if title and "Cennik" in title.get_text():
                cost_text = box.select_one("div.postContent__boxesText")
                if cost_text:
                    event_cost = cost_text.get_text(strip=True)
                break

        event_data = {
            "name": event_name,
            "event_link": event_link,
            "img": event_img,
            "description": event_description.get_text(strip=True)
            if event_description
            else None,
            "start_date": start_date,
            "end_date": end_date,
            "cost": event_cost
        }
        return event_data

    if config["labirynt_exhibitions"]["enabled"]:
        for event in tqdm(
            events,
            desc="Searching...",
            unit="event",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
            colour="green",
            ascii=True,
        ):
            data.append(scrape_event(event))
        for event in tqdm(
            future_events,
            desc="Searching...",
            unit="event",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
            colour="green",
            ascii=True,
        ):
            data.append(scrape_event(event))
    else:
        warn("Scraping labirynt_exhibitions is disabled in config")


    # at the end of the scraping loop add how many items were scraped and save the file
    with open(
        f"./data/{config['labirynt_exhibitions']['output']}", "w", encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success("Saved data to JSON files.")


# add this function to the upload handler at upload_select.py > sources
def upload_labirynt_exhibitions():
    config = load_config()
    config = config["scrapers"]
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    info("Uploading scraped (running events) data from site url")
    with open(f"./data/{config['labirynt_exhibitions']['output']}", "r") as f:
        events = json.load(f)

    for event in events:
        try:
            pocketbase.create_record(
                collection="collection_name", data=event, authorization=token
            )
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
