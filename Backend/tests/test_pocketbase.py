from os import getenv
from time import sleep

from dotenv import load_dotenv

from commands import auth
from utils.logmanager import error, info, success
from utils.pocketbase import create_record, delete_record, get_collection, get_record

load_dotenv()

collection = "test"
record_id = "28rs8m436gw04mf"


def test_pocketbase():
    pb = auth.pocketbaseLogin()
    token = pb.getAuthHeader()
    tests = [False, False, False, False]
    info("Starting pocketbase test")
    got_record = get_record(collection, record_id, authorization=token)
    if got_record:
        success(
            f"\nGot record with title of {got_record['name']}, {got_record['description']}"
        )
        tests[0] = True
    else:
        error("Failed to get record")
        tests[0] = False

    got_collection = get_collection(collection, authorization=token)
    if got_collection:
        success(f"\nGot collection with {got_collection['totalItems']} items")
        tests[1] = True
    else:
        error("Failed to get collection")
        tests[1] = False

    created_record = create_record(
        collection, {"name": "Test record"}, authorization=token
    )
    if created_record:
        success(f"\nCreated record with id of {created_record['id']}")
        tests[2] = True
    else:
        error("Failed to create record")
        tests[2] = False
    to_delete = ""
    if created_record:
        to_delete = created_record["id"]
    deleted_record = delete_record(to_delete, collection, authorization=token)
    if deleted_record:
        success(f"\nDeleted record with id of {to_delete}")
        tests[3] = True
    else:
        error("Failed to delete record")
        tests[3] = False

    if tests[0] and tests[1] and tests[2] and tests[3]:
        print()
        success("Pocketbase tests passed")
