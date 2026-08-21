import json
import os
from collections import Counter

from colorama import Fore, Style
from tqdm import tqdm

from commands.auth import pocketbaseLogin
from utils.logmanager import error, info, success, warn
from utils.pocketbase import (
    CollectionRequestError,
    PocketbaseCollectionResponse,
    create_record,
    get_collection,
)

# Definitions
#
filenames = ""
directory = ""
allowed_duplicates = ["zoom_running_d3313b8ee7d12d84", "zoom_running_e35ae8a445cde9cd"]
skipped_files = ["merged_input.json"]
directory = os.path.join(os.getcwd(), "data")


def load_files():
    input_data = []
    print()
    info("Trying to load files from local data/ folder...")
    filenames = os.listdir(directory)
    info(f"Found: {filenames}")

    for filename in filenames:
        if filename not in skipped_files:
            with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
                temp_data = json.load(f)
                input_data.extend(temp_data)
                info(f"Loaded {len(temp_data)} items from {filename}")
        else:
            continue
    success(f"Total list of items is {len(input_data)}")
    info("Check: checking for duplicate fingerprints")

    for item in tqdm(
        input_data, desc="Checking missing fingerprints", colour="MAGENTA"
    ):
        if "fingerprint" not in item:
            error(f"Item {item} has no fingerprint")

    counts = Counter(
        item["fingerprint"] for item in input_data if "fingerprint" in item
    )
    print()
    for fingerprint, count in counts.items():
        if count > 1 and fingerprint not in allowed_duplicates:
            warn(f"Found {count} duplicates for fingerprint {fingerprint}")
    success("Files loaded into array")
    return input_data


def _get_cur_data(token, page=1) -> PocketbaseCollectionResponse:
    try:
        return get_collection(
            collection="events", authorization=token, page=page, perPage=500
        )
    except CollectionRequestError as e:
        warn(e)
        return {"page": 0, "items": [], "perPage": 0, "totalItems": 0, "totalPages": 0}


def _get_existing_fingerprints(data):
    existing_fingerprints = set()
    for item in data:
        if "fingerprint" in item:
            existing_fingerprints.add(item["fingerprint"])
    return existing_fingerprints


def _clean_payload(event: dict) -> dict:
    cleaned = {}
    for key, value in event.items():
        if value is None:
            cleaned[key] = ""
            continue
        cleaned[key] = value
    return cleaned


def upload_merge():
    auth = pocketbaseLogin()
    token = auth.getAuthHeader()
    input_data: list[dict] = load_files()

    with open(os.path.join(directory, "merged_input.json"), "w") as f:
        try:
            json.dump(input_data, f, indent=4)
            info("Written input data to file")
        except Exception as e:
            error(f"Failed to write merged_input.json: {e}")

    info("Trying to get the current data from events collection...")
    data_response = _get_cur_data(token)
    current_data = []

    if data_response:
        current_data.extend(data_response["items"])
        if data_response["totalPages"] > 1:
            for page in range(2, data_response["totalPages"] + 1):
                data_response = _get_cur_data(token, page)
                current_data.extend(data_response["items"])

    info(f"Current data has {len(current_data)} items")
    existing_fingerprints = _get_existing_fingerprints(current_data)
    skipped = 0
    uploaded = 0
    failed = 0
    for event in tqdm(input_data, desc="Uploading events", colour="GREEN"):
        if event["fingerprint"] in existing_fingerprints:
            skipped += 1
            continue
        try:
            create_record(collection="events", data=event, authorization=token)
            uploaded += 1
        except Exception as e:
            # Extract PocketBase's detailed validation breakdown
            error_details = getattr(e, "data", getattr(e, "response", str(e)))
            error(f"Failed to upload event {event.get('name')}: {error_details}")
            failed += 1
    print(
        f"{Fore.GREEN}Uploaded {uploaded}{Style.RESET_ALL},{Fore.YELLOW} Skipped {skipped}{Style.RESET_ALL},{Fore.RED} Failed {failed}{Style.RESET_ALL}"
    )
