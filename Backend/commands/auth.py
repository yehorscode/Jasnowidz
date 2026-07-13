import requests

from utils.config import POCKETBASE_URL
from utils.logmanager import info, success, warn, error
import dotenv
from os import getenv
dotenv.load_dotenv()

def handle_login():
    print()
    info("Token will be regenerated on every auth request")
    pocketbaseLogin().auth()

class pocketbaseLogin():
    def __init__(self):
        self.email = getenv("AUTH_EMAIL")
        self.password = getenv("AUTH_PASSWORD")
        self.url = POCKETBASE_URL
        self.token = ""

    def auth(self, return_token=False):
        headers = {"Content-Type":"application/json"}
        data = {"identity":self.email, "password":self.password}
        request = requests.post(f"{self.url}/api/collections/users/auth-with-password", json=data, headers=headers)
        response = request.json()
        if request.status_code == 200:
            success(f"Authenticated and received a token {response["token"][:10]}...")
            if return_token:
                return response["token"]
            return
        else:
            error(f"{request.status_code} Failed to authenticate")
            return

    def getAuthHeader(self):
        return self.auth(return_token=True)
