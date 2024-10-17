import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    AUTH_URL = "https://github.com/login/oauth/authorize"
    API_URL = "https://api.github.com/user"
    CALLBACK_URL = (
        "http://localhost:8000/callback"  # Ensure this matches your OAuth app settings
    )
    BASE_DIR = os.path.join(os.path.expanduser("~"), ".sfss")
    STORAGE_DIR = os.path.join(
        BASE_DIR, "storage"
    )  # Helps to create folder storage in .sfss
    TOKENS_DIR = os.path.join(
        BASE_DIR, "tokens"
    )  # Helps to create folder tokens in .sfss
    ACTIVE_USER_FILE = os.path.join(BASE_DIR, "active_user.txt")
    LOG_FILE = os.path.join(BASE_DIR, "sfss.log")  # Location to say logging data
    AES_KEY_FILE = os.path.join(BASE_DIR, "aes.key")
