import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    CLIENT_ID = os.getenv("CLIENT_ID")
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
    BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000/api")
    DELTA_TOKEN_FILE = ".delta_token"