import os
import secrets
from pathlib import Path
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    TOKEN = os.getenv("TOKEN")
    APP_URL = os.getenv("APP_URL")
    EXPORT_DIR = Path("src/static/exports")
    TMP_DIR = Path("tmp")