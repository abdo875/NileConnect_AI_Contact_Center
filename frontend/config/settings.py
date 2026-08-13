import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
APP_NAME = "NileConnect AI Contact Center"
PAGE_ICON = "🌐"
