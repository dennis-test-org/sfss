import requests
import webbrowser
import secrets
import string
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
from config import Config
from logger import logger
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


class OAuthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Override to suppress HTTP server logs."""
        pass  # Suppress the default logging

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if "code" in params and "state" in params:
            self.server.auth_code = params["code"][0]
            self.server.auth_state = params["state"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authentication successful. You can close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authentication failed.")


def get_github_username(token):
    headers = {"Authorization": f"token {token}"}
    response = requests.get(Config.API_URL, headers=headers)
    response.raise_for_status()
    user_data = response.json()
    return user_data.get("login")


def authenticate():
    state = "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(16)
    )
    params = {
        "client_id": Config.GITHUB_CLIENT_ID,
        "redirect_uri": Config.CALLBACK_URL,
        "state": state,
        "scope": "read:user",
    }
    url = f"{Config.AUTH_URL}?{urlencode(params)}"
    webbrowser.open(url)
    logger.info("Opened browser for GitHub OAuth authentication.")

    server_address = ("localhost", 8000)
    server = HTTPServer(server_address, OAuthHandler)

    # Run the server in a separate thread to prevent blocking
    def run_server():
        try:
            server.handle_request()
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
        finally:
            server.server_close()  # Ensure socket is properly closed

    thread = threading.Thread(target=run_server)
    thread.start()
    thread.join()

    if hasattr(server, "auth_code") and server.auth_state == state:
        auth_code = server.auth_code
        token = get_access_token(auth_code)
        username = get_github_username(token)
        save_token(token, username)
        set_active_user(username)
        logger.info(f"User {username} authenticated successfully.")
        return token
    else:
        logger.error("Authentication failed or state mismatch.")
        return None


def get_access_token(code):
    headers = {"Accept": "application/json"}
    data = {
        "client_id": Config.GITHUB_CLIENT_ID,
        "client_secret": Config.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": Config.CALLBACK_URL,
    }
    response = requests.post(Config.TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    token = response.json().get("access_token")
    return token


def save_token(token, username):
    os.makedirs(Config.TOKENS_DIR, exist_ok=True)
    token_file = os.path.join(Config.TOKENS_DIR, f"{username}.env")
    with open(token_file, "w") as f:
        f.write(f"GITHUB_TOKEN={token}\n")
        f.write(
            f"AUTH_TIMESTAMP={datetime.now(timezone.utc).isoformat()}\n"
        )  # Use timezone-aware datetime
    logger.info(f"Token saved for user {username}.")


def set_active_user(username):
    with open(Config.ACTIVE_USER_FILE, "w") as f:
        f.write(username)
    logger.info(f"Active user set to {username}.")


def load_active_user():
    if not os.path.exists(Config.ACTIVE_USER_FILE):
        return None
    with open(Config.ACTIVE_USER_FILE, "r") as f:
        username = f.read().strip()
    return username


def load_token(username):
    token_file = os.path.join(Config.TOKENS_DIR, f"{username}.env")
    if not os.path.exists(token_file):
        return None
    with open(token_file, "r") as f:
        lines = f.readlines()
    token = None
    timestamp = None
    for line in lines:
        if line.startswith("GITHUB_TOKEN"):
            token = line.strip().split("=")[1]
        elif line.startswith("AUTH_TIMESTAMP"):
            timestamp = line.strip().split("=")[1]
    return token, timestamp


def is_authenticated():
    username = load_active_user()
    if not username:
        return False
    token_data = load_token(username)
    if not token_data:
        return False
    token, timestamp_str = token_data
    if not token or not timestamp_str:
        return False

    # Ensure auth_time is timezone-aware
    auth_time = datetime.fromisoformat(timestamp_str)
    if auth_time.tzinfo is None:
        auth_time = auth_time.replace(tzinfo=timezone.utc)

    current_time = datetime.now(timezone.utc)
    delta = current_time - auth_time

    if delta.total_seconds() > 300:
        logger.info(f"Authentication expired for user {username}.")
        return False
    return True


def get_current_user():
    username = load_active_user()
    if not username:
        return None
    token_data = load_token(username)
    if not token_data:
        return None
    token, timestamp_str = token_data
    return {
        "username": username,
        "token": token,
        "auth_time": datetime.fromisoformat(timestamp_str),
    }
