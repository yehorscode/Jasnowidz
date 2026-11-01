import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from tqdm import tqdm

from commands.auth import pocketbaseLogin
from utils import pocketbase
from utils.config import load_config, makedate
from utils.connecter import pget
from utils.headers import headers
from utils.logmanager import error, info, success, warn
from utils.pocketbase import create_record, gen_hash

MAX_WORKERS = 1


# Scraping scripts for zoom.lublin.pl
# id in config: zoom
def scrape_event(event):
    title_element = event.find("h3", class_="event-card__title")
    link_element = event.find("a", class_="event-card__image-link")
    place_element = event.find("div", class_="event-card__place")
    genre_element = event.find("div", class_="event-card__data-right").find("span")
    title = title_element.text.strip() if title_element else None
    link = link_element["href"] if link_element else None
    start_date = None
    end_date = None
    event_description = None
    date_spans = (
        event.find("div", class_="event-card__dates").find("p").find_all("span")
    )

    if len(date_spans) == 2:
        start_date, end_date = makedate(
            f"{date_spans[0].get_text()}{date_spans[1].get_text()}", source="zoom_event"
        )
    elif len(date_spans) == 1:
        start_date = makedate(date_spans[0].get_text(), source="zoom_event")
        if not isinstance(start_date, list):
            end_date = (
                datetime.fromisoformat(str(start_date)) + timedelta(hours=1)
            ).isoformat()
    else:
        tqdm.write("date_spans is empty or has more elements. Expected 2 or 1")
    if place_element:
        place = (
            place_element.find("span").text.strip()
            if place_element.find("span")
            else None
        )
    else:
        place = None
    genre = genre_element.text.strip() if genre_element else None

    link = link_element["href"] if link_element else None
    cost = None
    img_url = None
    if link:
        link_response = pget(link, headers=headers)
        if link_response.status_code == 200:
            link_soup = BeautifulSoup(link_response.content, "html.parser")
            # event_description = link_soup.find("div", class_="single-content")
            bilety_element = link_soup.find("p", text="Bilety:")
            if bilety_element:
                bilety_text = bilety_element.find_next("p")
                if bilety_text:
                    bilety_text = bilety_text.text.strip()
                else:
                    bilety_text = None
                cost = bilety_text
            img_element = link_soup.find("img", class_="glightbox-hero-image")
            img_url = img_element["src"] if img_element else None
        else:
            error(f"Error: {link_response.status_code}")

    # You (or me in the future) might ask:
    # "Why did you even add the array support for start dates?"
    # That's because some, very very rare cases return dates like these:
    # 2026-10-10 – 12:00, 13:00

    start_dates = start_date if isinstance(start_date, list) else [start_date]
    output = []
    for c_date in start_dates:
        if not c_date:
            continue

        current_end_date = end_date
        if isinstance(start_date, list) and not current_end_date:
            current_end_date = (
                datetime.fromisoformat(str(c_date)) + timedelta(hours=1)
            ).isoformat()
        event_data = {
            "name": title,
            "link": link,
            "location": place,
            "start_date": c_date,
            "end_date": current_end_date,
            "category": genre,
            "cost": cost,
            "image": img_url,
            "source": "zoom",
            "type": "event",
            "organizer": place,
            "description": event_description,
            "fingerprint": gen_hash(link, title, c_date, "zoom"),
        }
        output.append(event_data)

    return output


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
            if isinstance(data, list):
                results.extend(data)
            else:
                results.append(data)

        return results


def scrape_zoom():
    config = load_config()
    config = config["scrapers"]
    url = "https://zoom.lublin.pl/wydarzenia/"

    info(f"Starting diagnostics for: {url}")

    response = pget(url, headers=headers)
    if response.status_code != 200:
        error(f"Error while downloading {url}: {response.status_code}")
        return
    else:
        success("Page works")

    success("Checks ended")

    info(f"Scraping page: {url}")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    event_elements = soup.find("div", class_="archive-events__items")
    if event_elements is None:
        error("No events found")
        return
    else:
        event_elements = event_elements.find_all("div", class_="event-card-wrapper")

    info(f"Found {len(event_elements)} events.")

    data = []

    info("Starting search...")

    if config["zoom"]["enabled"]:
        data = run_parralel_scrape(event_elements)

        if len(data) == 0:
            error("No events found")
        else:
            success(f"Found {len(data)} events")
    else:
        warn("Scraping zoom data disabled in config")

    info("Event search ended.")

    with open(f"./data/{config['zoom']['output']}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success("Saved event files to json.")


def upload_zoom():
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    info("Uploading scraped data from zoom.lublin.eu")
    with open("./data/zoom_events.json", "r") as f:
        events = json.load(f)

    for event in events:
        try:
            create_record(collection="zoom", data=event, authorization=token)
        except pocketbase.CollectionOnlySuperusersError as e:
            error(f"You need superuser to upload {event['name']}: {e}")
            continue
        except pocketbase.CollectionCreateRecordError as e:
            error(f"Missing required values {event['name']}: {e}")
            continue
        except pocketbase.CollectionRequestError as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
