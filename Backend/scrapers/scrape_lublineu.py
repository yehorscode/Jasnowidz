import json
import tomllib
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from colorama import Back, Fore, Style
from tqdm import *

from commands.auth import pocketbaseLogin
from utils.config import load_config
from utils.headers import headers
from utils.logmanager import error, info, success, user_input, warn
from utils.pocketbase import create_record

# Scraping script for lublin.eu
# id in config: lublineu (main events), lublineu_running (for running/ongoing events)

# CONNECTIONS ARE BEING MADE UNSECURED ENSURE THAT SECURITY IS SECURE OR SOMETHING
# because lublin.eu has weird ssl certificates that i wasnt able to get working on two systems
# for this script and this script only the verification of SSL DISABLED


def scrape_lublineu():
    config = load_config()
    config = config["scrapers"]

    url = "https://lublin.eu/kultura/wydarzenia/"
    base_url = "https://lublin.eu"

    info(f"Started to scrape: {url}")

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        error(f"Error while loading {url}: {response.status_code}")
        return
    else:
        success("Page works")

    success("Diagnostics complete")

    info(f"Started scraping: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find_all("div", class_="event")

    data = []

    info("Finding all events...")

    if config["lublineu"]["enabled"]:
        for event in tqdm(
            event_elements,
            desc="Searching...",
            unit="event",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
            colour="green",
            ascii=True,
        ):
            event_place = "No data"
            event_organizer = "No data"
            event_participation = "No data"
            event_category = "No data"
            # Title and link
            title_div = event.find("div", class_="event-title")
            if title_div:
                title_a = title_div.find("a")
            else:
                title_a = None
            if title_a:
                event_title = title_a.get("title", "").strip()
                event_url = title_a.get("href", "").strip()
            else:
                event_title = "No title"
                event_url = "n/a"

            # Date and hour
            date_span = event.find("span", class_="event-date")
            time_span = event.find("span", class_="event-time")
            event_date = date_span.get_text(strip=True) if date_span else "No data"
            event_time = time_span.get_text(strip=True) if time_span else "No data"
            print("\n\n" + event_date + event_time + "\n\n")
            img_link = "None"
            full_event_url = f"{base_url}{event_url}" if event_url else "None"
            # Direct link to event page
            if full_event_url != "None":
                try:
                    event_response = requests.get(
                        full_event_url, headers=headers, verify=False
                    )
                    if event_response.status_code == 200:
                        event_soup = BeautifulSoup(
                            event_response.content, "html.parser"
                        )

                        img_element = event_soup.find("a", title="Baner promocyjny")
                        img_link = (
                            f"{base_url}{img_element['href']}" if img_element else None
                        )

                        # Clean label extraction
                        labels = event_soup.find_all("span", class_="label")
                        for label in labels:
                            label_text = label.text.strip()
                            val_elem = label.find_next_sibling("span")
                            val_text = val_elem.text.strip() if val_elem else "No data"

                            if "Data rozpoczęcia" in label_text:
                                event_date = val_text
                            elif "Godzina rozpoczęcia" in label_text:
                                event_time = val_text
                            elif "Miejsce" in label_text:
                                event_place = val_text
                            elif "Organizator" in label_text:
                                event_organizer = val_text
                            elif "Udział" in label_text:
                                event_participation = val_text
                            elif "Kategoria" in label_text:
                                event_category = val_text
                except requests.exceptions.RequestException:
                    warn(f"Can't fetch info for event url: {full_event_url}")

            iso_time = None
            local_tz = ZoneInfo("Europe/Warsaw")

            if event_date != "No data":
                try:
                    if event_time != "No data" and ":" in event_time:
                        combined_str = f"{event_date} {event_time}"
                        naive_dt = datetime.strptime(combined_str, "%Y-%m-%d %H:%M")
                    else:
                        naive_dt = datetime.strptime(event_date, "%Y-%m-%d")

                    utc_dt = naive_dt.replace(tzinfo=local_tz).astimezone(timezone.utc)
                    iso_time = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                except ValueError as e:
                    warn(f"Could not parse date/time for '{event_title}': {e}")
                    iso_time = None

            event_data = {
                "name": event_title,
                "date": event_date if "event_date" in locals() else "Brak dannych",
                "start_date": iso_time,
                "location": event_place if "event_place" in locals() else "No data",
                "organizer": event_organizer
                if "event_organizator" in locals()
                else "No data",
                "cost": event_participation
                if "event_participation" in locals()
                else "No data",
                "category": event_category
                if "event_category" in locals()
                else "No data",
                "link": full_event_url,
                "image": img_link,
            }

            data.append(event_data)

        info(f"Found {len(data)} events.")
        with open("./data/lublineu_events.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        warn("Scraping events from lublin.eu disabled in config")

    success("Scraping events finished!")

    if config["lublineu_running"]["enabled"]:
        info("Starting running event scrape...")

        cykliczne_section = soup.find("div", class_="events-groups-list")

        if not cykliczne_section:
            warn("Can't find 'Wydarzenia cykliczne' section")
        else:
            event_groups = cykliczne_section.find_all("div", class_="event-group")
            cykliczne_data = []

            for event in tqdm(
                event_groups,
                desc="Szukanie...",
                unit="wydarzenie",
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
                colour="green",
                ascii=True,
            ):
                link_element = event.find("a")
                if link_element:
                    start_date = "No data"
                    end_date = "No data"
                    event_place = "No data"
                    event_organizer = "No data"
                    event_participation = "No data"
                    event_category = "No data"
                    event_time = "No data"
                    event_title = link_element.get("title", "").strip()
                    event_url = link_element.get("href", "").strip()

                    expanded_scrape = requests.get(
                        f"https://lublin.eu{event_url}",
                        headers=headers,
                        verify=False,
                    )

                    if expanded_scrape.status_code != 200:
                        print(expanded_scrape.status_code)
                        warn(
                            f"Can't load event details for: https://lublin.eu{event_url}"
                        )
                        continue
                    elif expanded_scrape.status_code == 200:
                        expanded_soup = BeautifulSoup(
                            expanded_scrape.content, "html.parser"
                        )

                        labels = expanded_soup.find_all("span", class_="label")

                        for label in labels:
                            if label.text.strip() == "Data rozpoczęcia":
                                date_element = label.find_next_sibling("span")
                                start_date = (
                                    date_element.text.strip()
                                    if date_element
                                    else "No data"
                                )
                            elif label.text.strip() == "Data zakończenia":
                                date_element = label.find_next_sibling("span")
                                end_date = (
                                    date_element.text.strip()
                                    if date_element
                                    else "No data"
                                )
                            elif label.text.strip() == "Godzina rozpoczęcia":
                                time_element = label.find_next_sibling("span")
                                event_time = (
                                    time_element.text.strip()
                                    if time_element
                                    else "No data"
                                )
                            elif label.text.strip() == "Miejsce":
                                place_element = label.find_next_sibling("span")
                                event_place = (
                                    place_element.text.strip()
                                    if place_element
                                    else "No data"
                                )
                            elif label.text.strip().rstrip(":") == "Organizator":
                                organizer_element = label.find_next_sibling("span")
                                event_organizer = (
                                    organizer_element.text.strip()
                                    if organizer_element
                                    else "No data"
                                )
                            elif label.text.strip() == "Udział":
                                participation_element = label.find_next_sibling("span")
                                event_participation = (
                                    participation_element.text.strip()
                                    if participation_element
                                    else "No data"
                                )
                            elif label.text.strip() == "Kategoria":
                                category_element = label.find_next_sibling("span")
                                event_category = (
                                    category_element.text.strip()
                                    if category_element
                                    else "No data"
                                )

                    event_data = {
                        "name": event_title,
                        "link": f"https://lublin.eu{event_url}",
                        "start_date": start_date,
                        "end_date": end_date,
                        "time": event_time,
                        "place": event_place,
                        "organizer": event_organizer,
                        "participation": event_participation,
                        "category": event_category,
                    }
                    cykliczne_data.append(event_data)

            # Saving data
            with open(f"./data/{config['lublineu_running']['output']}", "w") as f:
                json.dump(cykliczne_data, f, ensure_ascii=False, indent=4)

            success(
                f"Saved {len(cykliczne_data)} running events to '{config['lublineu_running']['output']}'"
            )
        success(f"\nScraping {base_url} finished!")
    else:
        warn("Running events scrape is disabled in config")


def upload_lublineu():
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    config = load_config()
    config = config["scrapers"]
    info("Uploading scraped data from Lublin.eu")
    with open(f"./data/{config['lublineu']['output']}", "r") as f:
        events = json.load(f)
    with open(f"./data/{config['lublineu_running']['output']}", "r") as f:
        running = json.load(f)

    for event in running:
        try:
            create_record(collection="lubeu_running", data=event, authorization=token)
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
    for event in events:
        try:
            create_record(collection="lubeu_events", data=event, authorization=token)
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
