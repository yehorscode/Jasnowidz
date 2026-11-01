import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta

from bs4 import BeautifulSoup
from tqdm import tqdm

from commands.auth import pocketbaseLogin
from utils import pocketbase
from utils.config import (
    AI_URL,
    load_config,
    load_env,
    makedate,
    save_cache,
)
from utils.connecter import pget
from utils.headers import headers
from utils.logmanager import error, info, success, warn

# Scraping script for labirynt.com site
# id in config: labirynt_exhibitions (for exhibitios) labirynt_events (for events)

MAX_WORKERS = 20


last_parsed_event = 0


def scrape_event(event, ev_type):
    event_data = {}
    if ev_type == "exhb":
        start_date = None
        end_date = None
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
        full_event = pget(str(event_link), headers=headers)
        event_bs = BeautifulSoup(full_event.content, "html.parser")

        event_description = event_bs.find("div", class_="wysiwyg")
        event_place = event.find("p", class_="placeEvent-index")
        event_place = event_place.get_text(strip=True) if event_place else None
        event_duration = None
        event_duration = event_bs.find("p", class_="postContent__dateTitle")
        if event_duration:
            event_duration = event_duration.get_text(strip=True)
            start_date, end_date = makedate(
                date=event_duration, source="labirynt_exhibition"
            )
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
            "link": event_link,
            "image": event_img,
            "description": event_description.get_text(strip=True)
            if event_description
            else None,
            "start_date": start_date,
            "end_date": end_date,
            "cost": event_cost,
            "location": event_place,
            "type": "exhibition",
            "source": "labirynt",
            "category": "Wystawa",
            "organizer": event_place,
            "fingerprint": pocketbase.gen_hash(
                event_link, event_name, start_date, "labirynt"
            ),
        }
    elif ev_type == "evnt":
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

        full_event = pget(str(event_link), headers=headers)
        event_bs = BeautifulSoup(full_event.content, "html.parser")

        event_description = event_bs.find("div", class_="wysiwyg")
        event_place = event.find("p", class_="placeEvent-index")
        event_place = event_place.get_text(strip=True) if event_place else None

        # FIXED DATE PARSING
        event_duration = None
        date_p = event_bs.find("p", class_="postContent__dateTitle")
        event_duration = date_p.get_text(strip=True) if date_p else None

        start_date = None
        end_date = None

        if event_duration != None and event_duration != "":
            if " - " in event_duration:
                start_date, end_date = makedate(
                    date=event_duration, source="labirynt_event"
                )
            else:
                start_date = makedate(date=event_duration, source="labirynt_event")
                end_date = datetime.fromisoformat(str(start_date)) + timedelta(hours=1)
        event_cost = None
        for box in event_bs.select("div.postContent__box"):
            title = box.select_one("p.postContent__boxTitle")
            if title and "cennik" in title.get_text().lower():
                cost_text = box.select_one("div.postContent__boxesText")
                if cost_text:
                    event_cost = cost_text.get_text(strip=True)
                break
        if event_cost == "":
            event_cost = None

        event_data = {
            "name": event_name,
            "link": event_link,
            "image": event_img,
            "description": event_description.get_text(strip=True)
            if event_description
            else None,
            "start_date": start_date,
            "end_date": end_date,
            "cost": event_cost,
            "location": event_place,
            "type": "event",
            "source": "labirynt",
            "category": "Wydarzenie",
            "organizer": event_place,
            "fingerprint": pocketbase.gen_hash(
                event_link, event_name, start_date, "labirynt"
            ),
        }
    return event_data


def run_parralel_scrape(
    event_list,
    event_type,
    max_workers=MAX_WORKERS,
    last_parsed_event=last_parsed_event,
):
    counter = 0
    results = []
    if not event_list:
        return results
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_event = {
            executor.submit(scrape_event, event, event_type): event
            for event in event_list
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
                counter += 1
                last_parsed_event += 1

            if counter >= 10:
                to_save = {
                    "data": results,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "last_event": last_parsed_event,
                }
                save_cache(to_save, "labirynt_cache_unified.json")
                counter = 0

        return results


def scrape_labirynt_exhibitions():
    env = load_env()
    config = load_config()
    config = config["scrapers"]
    url = "https://labirynt.com/wystawy/"
    # base_url = "https://labirynt.com"

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
    future_content = pget("https://labirynt.com/wystawy/?future=true")
    soup = BeautifulSoup(content, "html.parser")
    future_soup = BeautifulSoup(future_content.content, "html.parser")
    data = []
    events = soup.find_all("div", class_="futureEvent")
    future_events = future_soup.find_all("div", class_="futureEvent")

    if config["labirynt_exhibitions"]["enabled"]:
        all_events = events + future_events
        data = run_parralel_scrape(all_events, event_type="exhb")
    else:
        warn("Scraping labirynt_exhibitions is disabled in config")

    # at the end of the scraping loop add how many items were scraped and save the file
    with open(
        f"./data/{config['labirynt_exhibitions']['output']}", "w", encoding="utf-8"
    ) as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    success(f"Saved {len(data)} entries to JSON files.")


def scrape_labirynt_events():
    env = load_env()
    config = load_config()
    config = config["scrapers"]
    url = "https://labirynt.com/wydarzenia"
    # base_url = "https://labirynt.com"
    # cache = load_cache("labirynt_events.json")
    # last_read = cache.get("last_read", 0) if cache else 0
    # last_parsed_event = last_read

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
    data = []
    events = soup.find_all("div", class_="futureEvent")
    if config["labirynt_events"]["enabled"]:
        data = run_parralel_scrape(events, event_type="evnt")
    else:
        warn("Scraping labirynt_events is disabled in config")

    # at the end of the scraping loop add how many items were scraped and save the file
    with open(
        f"./data/{config['labirynt_events']['output']}", "w", encoding="utf-8"
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
        except pocketbase.CollectionOnlySuperusersError as e:
            error(f"You need superuser to upload {event['name']}: {e}")
            continue
        except pocketbase.CollectionCreateRecordError as e:
            error(f"Missing required values {event['name']}: {e}")
            continue
        except pocketbase.CollectionRequestError as e:
            error(f"Failed to upload event {event['name']}: {e}")
            continue
