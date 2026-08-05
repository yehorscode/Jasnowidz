import json

import certifi
import requests
from bs4 import BeautifulSoup
from colorama import Back, Fore, Style
from tqdm import *

from commands.auth import pocketbaseLogin
from utils.headers import headers
from utils.logmanager import error, info, success, user_input, warn
from utils.pocketbase import create_record

# CONNECTIONS ARE BEING MADE UNSECURED ENSURE THAT SECURITY IS SECURE OR SOMETHING
# because lublin.eu has weird ssl certificates that i wasnt able to get working on two systems
# for this script and this script only the verification of SSL DISABLED


def scrape_lublineu():
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

    # Początek scrapowania strony lublina
    # Potrzebne dane:
    # Nazwa, Data, Godzina Rozpoczęcia, Miejsce, Udział (Platny, Darmowy, Zapisy), Kategoria, Link bezpośredni
    # Wydarzenia Cykliczne lublin.eu:
    # Nazwa

    info(f"Started scraping: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find_all("div", class_="event")

    data = []

    info("Finding all events...")

    for event in tqdm(
        event_elements,
        desc="Searching...",
        unit="event",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} {unit} • {elapsed} elapsed • {remaining} remaining",
        colour="green",
        ascii=True,
    ):
        event_date = "No data"
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
        event_time = time_span.text.strip() if time_span else "No time found"

        # Direct link to event page
        full_event_url = f"https://lublin.eu{event_url}"
        try:
            event_response = requests.get(full_event_url, headers=headers, verify=False)
        except requests.exceptions.RequestException:
            warn(f"Can't fetch info for event url: {full_event_url}")
            continue
        if event_response.status_code != 200:
            warn(f"Can't fetch info for event url: {full_event_url}")
            continue

        event_soup = BeautifulSoup(event_response.content, "html.parser")

        labels = event_soup.find_all("span", class_="label")

        for label in labels:
            if label.text.strip() == "Data rozpoczęcia":
                date_element = label.find_next_sibling("span")
                event_date = date_element.text.strip() if date_element else "No data"
            elif label.text.strip() == "Godzina rozpoczęcia":
                time_element = label.find_next_sibling("span")
                event_time = time_element.text.strip() if time_element else "No data"
            elif label.text.strip() == "Miejsce":
                place_element = label.find_next_sibling("span")
                event_place = place_element.text.strip() if place_element else "No data"
            elif label.text.strip() == "Organizator":
                organizer_element = label.find_next_sibling("span")
                event_organizer = (
                    organizer_element.text.strip() if organizer_element else "No data"
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
                    category_element.text.strip() if category_element else "No data"
                )

        combined_time = ""
        if event_date != "No data" and event_time != "No data":
            combined_time = f"{event_date} {event_time}"
            print(combined_time)
        # Tworzenie słownika dla wydarzenia
        event_data = {
            "name": event_title,
            "date": event_date if "event_date" in locals() else "Brak dannych",
            "start_date": combined_time,
            "location": event_place if "event_place" in locals() else "No data",
            "organizer": event_organizer
            if "event_organizator" in locals()
            else "No data",
            "cost": event_participation
            if "event_participation" in locals()
            else "No data",
            "category": event_category if "event_category" in locals() else "No data",
            "link": full_event_url,
        }

        data.append(event_data)

    # Wyświetlanie wyników
    info(f"Found {len(data)} events.")
    with open("./data/lublin_eu_data.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success("Scraping events finished!")

    # Scrapowanie wydarzeń cyklicznych
    info("Starting repeating event scrape...")

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
                    warn(f"Can't load event details for: https://lublin.eu{event_url}")
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
                                date_element.text.strip() if date_element else "No data"
                            )
                        elif label.text.strip() == "Data zakończenia":
                            date_element = label.find_next_sibling("span")
                            end_date = (
                                date_element.text.strip() if date_element else "No data"
                            )
                        elif label.text.strip() == "Godzina rozpoczęcia":
                            time_element = label.find_next_sibling("span")
                            event_time = (
                                time_element.text.strip() if time_element else "No data"
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

                # Tworzenie słownika dla wydarzenia cyklicznego
                event_data = {
                    "name": event_title,
                    "link": f"https://lublin.eu{event_url}",  # direct link to site
                    "start_date": start_date,
                    "end_date": end_date,
                    "time": event_time,
                    "place": event_place,
                    "organizer": event_organizer,
                    "participation": event_participation,
                    "category": event_category,
                }
                cykliczne_data.append(event_data)

        # Zapisanie danych do pliku JSON
        with open("./data/lublin_eu_cykliczne.json", "w") as f:
            json.dump(cykliczne_data, f, ensure_ascii=False, indent=4)

        success(
            f"Saved {len(cykliczne_data)} repeating events to './data/lublin_eu_cykliczne.json'"
        )
    success(f"\nScraping {base_url} finished!")


def upload_lublineu():
    auth = pocketbaseLogin()
    token=auth.getAuthHeader()
    info("Uploading scraped data from Lublin.eu")
    with open("./data/lublin_eu_data.json", "r") as f:
        events = json.load(f)
    with open("./data/lublin_eu_cykliczne.json", "r") as f:
        cykliczne = json.load(f)

    for event in events:
        try:
            create_record(collection="lubeu_cykliczne",data=event,authorization=token)
        except Exception as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
