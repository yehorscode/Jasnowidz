import json

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from tqdm import *

from commands.auth import pocketbaseLogin
from utils import pocketbase
from utils.config import load_config, makedate
from utils.connecter import pget
from utils.headers import headers
from utils.logmanager import error, info, success, warn
from utils.pocketbase import create_record, gen_hash

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

    response = pget(url, headers=headers)
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
            event_time = None
            event_end_time = None
            event_place = None
            event_organizer = None
            event_participation = None
            event_category = None
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
                event_title = None
                event_url = None

            img_link = None
            full_event_url = f"{base_url}{event_url}" if event_url else None
            # Direct link to event page
            if full_event_url != None:
                try:
                    event_response = pget(full_event_url, headers=headers)
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
                            val_text = val_elem.text.strip() if val_elem else None

                            if "Data rozpoczęcia" in label_text:
                                event_date = val_text
                            elif "Godzina rozpoczęcia" in label_text:
                                event_time = val_text
                            elif "Godzina zakończenia" in label_text:
                                event_end_time = val_text
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

            dates_array: list[Tag] = event.find(
                "div", class_="event-date-time"
            ).find_all("span")
            start_date = dates_array[0].text.strip()
            end_date = dates_array[1].text.strip()
            success(f"{start_date}  {event_time}")
            if event_time:
                start_date = makedate(
                    source="lublineu_event", date=start_date, time=event_time
                )
            if event_end_time:
                end_date = makedate(
                    source="lublineu_event", date=end_date, time=event_end_time
                )

            event_data = {
                "name": event_title,
                "start_date": start_date,
                "end_date": end_date,
                "location": event_place if "event_place" in locals() else None,
                "organizer": event_organizer,
                "cost": event_participation,
                "category": event_category,
                "link": full_event_url,
                "image": img_link,
                "source": "lublin_eu",
                "type": "event",
                "fingerprint": gen_hash(
                    full_event_url, event_title, start_date, "lublin_eu"
                ),
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
                    start_date = None
                    end_date = None
                    event_place = None
                    event_organizer = None
                    event_participation = None
                    event_category = None
                    event_time = None
                    event_title = link_element.get("title", "").strip()
                    event_url = link_element.get("href", "").strip()
                    raw_start_date = None
                    expanded_scrape = pget(
                        f"https://lublin.eu{event_url}",
                        headers=headers,
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
                            if label.text.strip() == "Godzina rozpoczęcia":
                                time_element = label.find_next_sibling("span")
                                event_time = (
                                    time_element.text.strip() if time_element else None
                                )
                            elif label.text.strip() == "Data rozpoczęcia":
                                date_element = label.find_next_sibling("span")
                                raw_start_date = (
                                    date_element.text.strip() if date_element else None
                                )

                            elif label.text.strip() == "Data zakończenia":
                                date_element = label.find_next_sibling("span")
                                raw_end_date = (
                                    date_element.text.strip() if date_element else None
                                )

                                end_date = (
                                    makedate(
                                        date=raw_end_date, source="lublineu_running"
                                    )
                                    if raw_end_date is not None
                                    else None
                                )

                            elif label.text.strip() == "Miejsce":
                                place_element = label.find_next_sibling("span")
                                event_place = (
                                    place_element.text.strip()
                                    if place_element
                                    else None
                                )
                            elif label.text.strip().rstrip(":") == "Organizator":
                                organizer_element = label.find_next_sibling("span")
                                event_organizer = (
                                    organizer_element.text.strip()
                                    if organizer_element
                                    else None
                                )
                            elif label.text.strip() == "Udział":
                                participation_element = label.find_next_sibling("span")
                                event_participation = (
                                    participation_element.text.strip()
                                    if participation_element
                                    else None
                                )
                            elif label.text.strip() == "Kategoria":
                                category_element = label.find_next_sibling("span")
                                event_category = (
                                    category_element.text.strip()
                                    if category_element
                                    else None
                                )

                    if event_time:
                        makedate(
                            source="lublineu_event",
                            date=str(raw_start_date),
                            time=event_time,
                        )

                    event_data = {
                        "name": event_title,
                        "link": f"https://lublin.eu{event_url}",
                        "start_date": start_date,
                        "end_date": end_date,
                        "location": event_place,
                        "organizer": event_organizer,
                        "participation": event_participation,
                        "category": event_category,
                        "source": "lublin_eu",
                        "type": "running_event",
                        "fingerprint": gen_hash(
                            link=f"https://lublin.eu{event_url}",
                            name=event_title,
                            start_date=start_date,
                            source="lublin_eu",
                        ),
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
        except pocketbase.CollectionOnlySuperusersError as e:
            error(f"You need superuser to upload {event['name']}: {e}")
            continue
        except pocketbase.CollectionCreateRecordError as e:
            error(f"Missing required values {event['name']}: {e}")
            continue
        except pocketbase.CollectionRequestError as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue

    for event in events:
        try:
            create_record(collection="lubeu_events", data=event, authorization=token)
        except pocketbase.CollectionOnlySuperusersError as e:
            error(f"You need superuser to upload {event['name']}: {e}")
            continue
        except pocketbase.CollectionCreateRecordError as e:
            error(f"Missing required values {event['name']}: {e}")
            continue
        except pocketbase.CollectionRequestError as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
