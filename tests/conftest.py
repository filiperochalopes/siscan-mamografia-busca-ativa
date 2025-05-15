import pytest
from playwright.sync_api import Page
from dotenv import load_dotenv
import os

load_dotenv()

APP_URL = os.getenv("APP_URL")
TOKEN = os.getenv("TOKEN")
TEST_FILES_DIR = os.getenv("TEST_FILES_DIR", "tests/files")


@pytest.fixture
def logged_in_page(page: Page) -> Page:
    """Faz login e retorna a página já logada."""
    print(f"[FIXTURE] Acessando {APP_URL}...")
    page.goto(APP_URL)

    print("[FIXTURE] Aguardando input de token aparecer...")
    page.wait_for_selector('input[name="token"]', timeout=5000)

    print("[FIXTURE] Preenchendo o token correto...")
    page.fill('input[name="token"]', TOKEN)

    print("[FIXTURE] Clicando no botão Entrar e aguardando navegação...")
    with page.expect_navigation(timeout=10000):
        page.click('button[type="submit"]')

    print("[FIXTURE] Login realizado com sucesso!")
    return page
