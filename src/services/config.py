import os
import secrets
from pathlib import Path

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    TOKEN = os.getenv("TOKEN")
    APP_URL = os.getenv("APP_URL")
    TEST_FILES_DIR = os.getenv("TEST_FILES_DIR")
    EXPORT_DIR = Path("src/static/exports")
    TMP_DIR = Path("tmp")
