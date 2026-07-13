from .config import POCKETBASE_URL, COLLECTIONS
import requests
from utils.logmanager import info, success, error
import json
def get_collection(collection: str, page = 1, authorization = None, perPage = None, sort = None, filter = None, ) -> dict | None:
    if collection not in COLLECTIONS:
        error(f"Collection {collection} doesnt exist")
        return None
    else:
        headers = {"Authorization": authorization}
        request = f"{POCKETBASE_URL}/api/collections/{collection}/records"
        if page:
            request += f"?page={page}"
        if perPage:
            request += f"?perPage={perPage}"
        if sort:
            request += f"?sort={sort}"
        if filter:
            request += f"?filter={filter}"

        request = requests.get(request, headers=headers)

        if request.status_code == 200:
            success(f"Successfully fetched collection {collection}, {request.request}")
            return request.json()
        elif request.status_code == 400:
            error(f"Error 400, something went wrong with {request.request}")
            return None
        elif request.status_code == 403:
            error(f"Error 403, only superusers can access this action {request.request}")
            return None

def get_record(collection: str, record_id: str, fields = None, authorization = None):
    if collection not in COLLECTIONS:
        error(f"Collection {collection} doesnt exist")
        return None
    else:
        headers = {"Authorization": authorization}
        request = f"{POCKETBASE_URL}/api/collections/{collection}/records/{record_id}"
        if fields:
            request += f"?fields={fields}"
        request = requests.get(request, headers=headers)
        if request.status_code == 200:
            success(f"Successfully fetched record {record_id} from collection {collection}")
            return request.json()
        elif request.status_code == 400:
            error(f"Error 400, something went wrong with {request.request}")
            return None
        elif request.status_code == 403:
            error(f"Error 403, only superusers can access this action {request.request}")
            return None

def create_record(collection: str, data: dict, authorization = None, content_type:str = "application/json"):
    if collection not in COLLECTIONS:
        error(f"Collection {collection} doesnt exist")
        return None
    else:
        if authorization:
            headers = {"Content-Type": content_type, "Authorization": authorization}
        else:
            headers = {"Content-Type": content_type}
        request = f"{POCKETBASE_URL}/api/collections/{collection}/records"
        request = requests.post(request, headers=headers, json=data)
        if request.status_code == 200:
            success(f"Successfully created record in collection {collection}, {request.request}")
            return request.json()
        elif request.status_code == 400:
            error(f"Error 400, something went wrong with {request.request}")
            return None
        elif request.status_code == 403:
            error(f"Error 403, only superusers can access this action {request.request}")
            return None

def delete_record(record_id: str, collection:str, authorization = None) -> bool:
    if collection not in COLLECTIONS:
        error(f"Collection {collection} doesnt exist")
        return False
    else:
        if authorization:
            headers = {"Authorization": authorization}
        request = requests.delete(f"{POCKETBASE_URL}/api/collections/{collection}/records/{record_id}", headers=headers)
        if request.status_code == 204:
            success(f"Record {record_id} from collection {collection} deleted")
            return True
        elif request.status_code == 400:
            error(f"Failed to delete {record_id}: Make sure that the record is not part of a required relation reference")
            return False
        elif request.status_code == 403:
            error(f"Failed to delete {record_id}: Only superusers can access this action")
            return False
        elif request.status_code == 404:
            error(f"Failed to delete {record_id}: The requested resource wasn't found")
            return False
