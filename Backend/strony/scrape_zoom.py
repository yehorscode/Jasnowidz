import json

import requests
from bs4 import BeautifulSoup
from colorama import Back, Fore, Style
from tqdm import tqdm

from commands.auth import pocketbaseLogin
from utils.headers import headers
from utils.logmanager import error, info, success, warn
from utils.pocketbase import create_record


def scrape_zoom():
    url = "https://zoom.lublin.pl/wydarzenia/"
    base_url = "https://zoom.lublin.pl"

    info(f"Starting diagnostics for: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        error(f"Error while downloading {url}: {response.status_code}")
        return
    else:
        success("Page works")

    success("Checks ended")

    # Potrzebne dane
    # nazwa, adres, daty, link, gatunek

    info(f"Scraping page: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find("div", class_="archive-events__items").find_all(
        "div", class_="event-card-wrapper"
    )

    info(f"Found {len(event_elements)} events.")

    data = []
    bajka_data = []

    info("Starting search...")

    for event in tqdm(
        event_elements,
        desc="Searching...",
        unit="event",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
        colour="green",
        ascii=True,
    ):
        title_element = event.find("h3", class_="event-card__title")
        link_element = event.find("a", class_="event-card__image-link")
        place_element = event.find("div", class_="event-card__place")
        time_element = event.find("div", class_="event-card__dates").find("span")
        genre_element = event.find("div", class_="event-card__data-right").find("span")

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

        link = link_element["href"] if link_element else None

        event_data = {
            "name": title,
            "link": link,
            "location": place,
            "start_date": time,
            "category": genre,
            "cost": None,
        }

        if link:
            # Wykonaj dodatkowy request do linku
            link_response = requests.get(link, headers=headers)
            if link_response.status_code == 200:
                # Scrapuj potrzebne dane z linku
                link_soup = BeautifulSoup(link_response.content, "html.parser")
                bilety_element = link_soup.find("p", text="Bilety:")
                if bilety_element:
                    bilety_text = bilety_element.find_next("p").text.strip()
                    event_data["cost"] = bilety_text
            else:
                error(f"Error: {link_response.status_code}")

        data.append(event_data)

        if place == "Kino Bajka":
            bajka_data.append(event_data)

    if len(data) == 0:
        error(f"No events found")
    else:
        success(f"Found {len(data)} events")

    if len(bajka_data) == 0:
        warn("No events in Kino Bajka")
    else:
        success(f"Found {len(bajka_data)} events in Kino Bajka")

    info("Event search ended.")

    with open("./data/zoom_events.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    with open("./data/zoom_bajka_events.json", "w", encoding="utf-8") as f:
        json.dump(bajka_data, f, ensure_ascii=False, indent=4)

    success("Saved event files to json.")


def upload_zoom():
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    info("Uploading scraped data from zoom.lublin.eu")
    with open("./data/zoom_events.json", "r") as f:
        events = json.load(f)
    # with open("./data/lublin_eu_cykliczne.json", "r") as f:
    #     cykliczne = json.load(f)

    for event in events:
        try:
            create_record(collection="zoom", data=event, authorization=token)
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
