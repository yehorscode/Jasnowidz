import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from colorama import Back, Fore, Style
from tqdm import *

from commands.auth import pocketbaseLogin
from utils.config import load_config
from utils.headers import headers
from utils.logmanager import error, info, success, warn
from utils.pocketbase import create_record, gen_hash

# Scraping script for zoom.lublin.pl running events
# id in config: zoom_running


def scrape_event(event):
    title_element = event.find("h3", class_="event-card__title")
    link_element = event.find("a", class_="event-card__image-link")
    place_element = event.find("div", class_="event-card__place")
    time_element = event.find("div", class_="event-card__dates").find("span")
    genre_element = event.find("div", class_="event-card__data-right").find("span")
    image_link = event.find("img").get("src")
    title = title_element.text.strip() if title_element else None
    link = link_element["href"] if link_element else None
    if place_element:
        place = (
            place_element.find("span").text.strip()
            if place_element.find("span")
            else None
        )
    else:
        place = None
    time = time_element.text.strip() if time_element else None
    genre = genre_element.text.strip() if genre_element else None

    link = str(link_element["href"]) if link_element else "None"

    expanded_event = requests.get(link, headers=headers)
    cost = None
    description = None

    if link:
        try:
            link_response = requests.get(link, headers=headers, timeout=10)
            if link_response.status_code == 200:
                link_soup = BeautifulSoup(link_response.content, "html.parser")

                single_content = link_soup.find("div", class_="single-content")
                if single_content:
                    p_tag = single_content.find("p")
                    description = p_tag.text.strip() if p_tag else None

                bilety_element = link_soup.find("p", string="Bilety:")
                if bilety_element:
                    next_p = bilety_element.find_next("p")
                    cost = next_p.text.strip() if next_p else None
            else:
                error(f"Error while loading link ({link}): {link_response.status_code}")
        except Exception as e:
            error(f"Request failed for {link}: {e}")

    event_data = {
        "name": title,
        "link": link,
        "location": place,
        "start_date": time,
        "category": genre,
        "cost": cost,
        "image": image_link,
        "description": description,
        "source": "zoom",
        "type": "running",
        "fingerprint": gen_hash(link, title, "zoom_running")
    }
    return event_data


MAX_WORKERS = 5


def run_parralel_scrape(event_list, max_workers=MAX_WORKERS):
    results = []
    if not event_list:
        return results
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_event = {
            executor.submit(scrape_event, event): event for event in event_list
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


def scrape_zoom_running():
    config = load_config()
    config = config["scrapers"]
    url = "https://zoom.lublin.pl/w-trakcie/"

    info(f"Started diagnostics for: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        error(f"Error while loading {url}: {response.status_code}")
        return
    else:
        success("Page works")

    success("Diagnostics ended!")

    info(f"Started scraping: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find("div", class_="archive-events__items")

    if event_elements:
        event_elements = event_elements.find_all("div", class_="event-card-wrapper")
    else:
        event_elements = []

    info(f"Found {len(event_elements)} events.")

    data = []

    info("Started event search...")
    if config["zoom_running"]["enabled"]:
        data = run_parralel_scrape(event_elements)

        if len(data) == 0:
            error("No events found")
        else:
            success(f"Found {len(data)} events")

        info("Event search ended.")

        with open(
            f"./data/{config['zoom_running']['output']}", "w", encoding="utf-8"
        ) as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        success("Saved data to JSON files.")
    else:
        warn("Scraping repeating event data from zoom disabled")


def upload_zoom_running():
    config = load_config()
    config = config["scrapers"]
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    info("Uploading scraped (running events) data from zoom.lublin.eu/w-trakcie")
    with open(f"./data/{config['zoom_running']['output']}", "r") as f:
        events = json.load(f)

    for event in events:
        try:
            create_record(collection="zoom", data=event, authorization=token)
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
