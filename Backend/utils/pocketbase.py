from typing import TypedDict, cast

import requests

from utils.logmanager import error, info, success

from .config import POCKETBASE_URL, load_config


class CollectionRequestError(Exception):
    """Something went wrong while processing your request"""


class CollectionRecordNotFoundError(Exception):
    """Requested record can't be found in the requested collection"""


class CollectionNotFoundError(Exception):
    """Collection isn't present in collections array"""


class CollectionOnlySuperusersError(Exception):
    """Only superusers can access this action"""


class CollectionCreateRecordError(Exception):
    """Missing required values"""


class CollectionBatchError(Exception):
    """Something went wrong while processing a batch request"""


class PocketbaseCollectionResponse(TypedDict):
    page: int
    perPage: int
    totalPages: int
    totalItems: int
    items: list[dict]


# config load
cfg = load_config()
collections = []
if cfg.get("collections"):
    collections: list = cfg.get("collections", [])
else:
    collections = []
    error("No collections set in config")

import hashlib


def gen_hash(link, name, start_date, source: str) -> str:
    normalized = f"{name.strip().lower()}|{start_date}|{link}"
    hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    hash = source + "_" + hash
    # info(f"Generated hash {hash}")
    return f"{hash}"


def build_headers(
    authorization: str | None = None, content_type: str = "application/json"
) -> dict[str, str]:
    headers = {"Content-Type": content_type}
    if authorization:
        headers["Authorization"] = authorization
    return headers


# list/search collection
def get_collection(
    collection: str,
    page=1,
    authorization=None,
    perPage=None,
    sort=None,
    filter=None,
) -> PocketbaseCollectionResponse:
    """Gets items from a collection
    Args:
        collection: string
        page: int
        authorization: string
        perPage: int
        sort: string
        filter: string
    Returns:
        PocketbaseCollectionResponse
    """
    if collection not in collections:
        raise CollectionNotFoundError(f"Collection {collection} doesnt exist")

    request = f"{POCKETBASE_URL}/api/collections/{collection}/records"
    query_params = {
        k: v
        for k, v in {
            "page": page,
            "perPage": perPage,
            "sort": sort,
            "filter": filter,
        }.items()
        if v is not None
    }
    response = requests.get(
        request, headers=build_headers(authorization), params=query_params
    )

    if response.status_code == 200:
        return cast(PocketbaseCollectionResponse, response.json())
    elif response.status_code == 403:
        raise CollectionOnlySuperusersError(
            f"Error 403, only superusers can access this action {response.request}"
        )
    elif response.status_code == 400:
        raise CollectionRequestError(
            f"Error 400, Something went wrong while processing your request {response.request}"
        )
    else:
        raise CollectionRequestError(
            f"Error {response.status_code}, something went wrong with {response.request}"
        )


def get_record(
    collection: str, record_id: str, fields=None, authorization=None
) -> dict:
    """Gets a record from a collection by it's record_id
    Args:
        collection: str
        record_id: str
        ?fields: str
        ?authorization: str
    Returns:
        record: dict
    """
    if collection not in collections:
        raise CollectionNotFoundError(f"Collection {collection} doesnt exist")

    query_params = {
        k: v
        for k, v in {
            "fields": fields,
        }.items()
        if v is not None
    }
    request = f"{POCKETBASE_URL}/api/collections/{collection}/records/{record_id}"

    response = requests.get(
        request,
        headers=build_headers(authorization, "application/json"),
        params=query_params,
    )

    if response.status_code == 200:
        # success(f"Successfully fetched record {record_id} from collection {collection}")
        return cast(dict, response.json())
    elif response.status_code == 403:
        raise CollectionOnlySuperusersError(
            f"Error 403, only superusers can access this action {response.request}"
        )
    elif response.status_code == 404:
        raise CollectionRecordNotFoundError(
            f"Error 404, requested record cannot be found {response.request}"
        )
    else:
        raise CollectionRequestError(
            f"Error {response.status_code}, something went wrong with {response.request}"
        )


def create_record(
    collection: str,
    data: dict,
    authorization=None,
    content_type: str = "application/json",
) -> dict:
    if collection not in collections:
        raise CollectionNotFoundError(f"Collection {collection} doesnt exist")

    request = f"{POCKETBASE_URL}/api/collections/{collection}/records"

    response = requests.post(
        request, headers=build_headers(authorization, content_type), json=data
    )
    if response.status_code == 200:
        # success(
        #     f'Successfully created record {response.json()["id"]} at collection "{response.json()["collectionName"]}"'
        # )
        return cast(dict, response.json())
    elif response.status_code == 403:
        raise CollectionOnlySuperusersError(
            f"Error 403, only superusers can access this action {response.request}"
        )
    elif response.status_code == 400:
        raise CollectionCreateRecordError(
            f"Missing required values or not authorized to create record {response.request}"
        )
    else:
        raise CollectionRequestError(
            f"Error {response.status_code}, something went wrong with {response.request}"
        )


def delete_record(record_id: str, collection: str, authorization=None) -> bool:
    if collection not in collections:
        raise CollectionNotFoundError(f"Collection {collection} doesn't exist")

    response = requests.delete(
        f"{POCKETBASE_URL}/api/collections/{collection}/records/{record_id}",
        headers=build_headers(authorization, "None"),
    )
    if response.status_code == 204:
        success(f"Record {record_id} from collection {collection} deleted")
        return True
    elif response.status_code == 400:
        raise CollectionRequestError(
            f"Failed to delete record. Make sure that the record is not part of a required relation reference {response.request}"
        )
    elif response.status_code == 403:
        raise CollectionOnlySuperusersError(
            f"Failed to delete {record_id}: Only superusers can access this action"
        )
    elif response.status_code == 404:
        raise CollectionRecordNotFoundError(
            f"Failed to delete {record_id}: The requested resource wasn't found"
        )
    else:
        return False
