from colorama import Back, Fore, Style

from commands.auth import pocketbaseLogin
from utils.config import COLLECTIONS
from utils.logmanager import info, success, warn
from utils.pocketbase import CollectionRequestError, delete_record, get_collection


def delete_all_records():
    ath = pocketbaseLogin()
    token = ath.getAuthHeader()
    for collection in COLLECTIONS:
        if collection == "test":
            continue
        else:
            try:
                records = get_collection(collection=collection, authorization=token)
                print(records)
                totalItems = 0
                totalPages = 0
                curPage = 1
                itemids = []
                if records["totalItems"] != 0:
                    totalItems = records["totalItems"]
                    totalPages = records["totalPages"]
                else:
                    continue
                for item in records["items"]:
                    itemids.append(item["id"])
                while curPage != totalPages:
                    curPage += 1
                    nxtpg = get_collection(
                        collection=collection, authorization=token, page=curPage
                    )
                    for item in nxtpg["items"]:
                        itemids.append(item["id"])
                info(
                    f"{Back.LIGHTRED_EX}Will delete {totalItems} items{Style.RESET_ALL}"
                )
                for to_del_id in itemids:
                    delete_record(
                        record_id=to_del_id, collection=collection, authorization=token
                    )

                continue
            except CollectionRequestError as e:
                print(e)

def delete_local_data():
    import os
    import shutil

    if os.path.exists("./data"):
        shutil.rmtree("./data")
        success("Deleted all local data from ./data")
    else:
        warn("No data available")
