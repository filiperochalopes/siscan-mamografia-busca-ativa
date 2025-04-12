from playwright.sync_api import Page
import secrets
from .conftest import APP_URL

def test_login_com_token_incorreto(page: Page):
    fake_token = secrets.token_hex(16)
    print(f"[DEBUG] Token gerado para teste: {fake_token}")

    print(f"[DEBUG] Acessando {APP_URL}...")
    page.goto(APP_URL)

    print("[DEBUG] Aguardando input de token aparecer...")
    page.wait_for_selector('input[name="token"]', timeout=5000)

    print("[DEBUG] Preenchendo o token falso...")
    page.fill('input[name="token"]', fake_token)

    print("[DEBUG] Clicando no botão Entrar...")
    page.click('button[type="submit"]')

    print("[DEBUG] Aguardando mensagem de erro aparecer...")
    page.wait_for_selector("p.text-red-500", timeout=5000)

    print("[DEBUG] Capturando a mensagem de erro...")
    error_message = page.text_content("p.text-red-500")
    print(f"[DEBUG] Mensagem encontrada: {error_message}")

    assert "Token incorreto" in error_message, (
        f"Mensagem de erro inesperada: {error_message}"
    )

def test_upload_arquivo_invalido_mostra_erro(logged_in_page: Page):
    print("[DEBUG] Aguardando área de upload aparecer...")
    logged_in_page.wait_for_selector("span", timeout=5000)

    print("[DEBUG] Tentando fazer upload de um arquivo inválido (.txt)...")
    upload_input = logged_in_page.query_selector('input[type="file"]')
    upload_input.set_input_files(
        "tests/files/example.txt"
    )  # Você deve ter esse arquivo

    print("[DEBUG] Clicando no botão Enviar...")
    logged_in_page.click('button[type="submit"]')

    print("[DEBUG] Aguardando mensagem de erro...")
    logged_in_page.wait_for_selector("div.text-red-500 p", timeout=5000)

    error_message = logged_in_page.text_content("div.text-red-500 p")
    print(f"[DEBUG] Mensagem de erro encontrada: {error_message}")

    assert "Formato de arquivo inválido" in error_message, (
        f"Mensagem de erro inesperada: {error_message}"
    )


def test_upload_pdf_invalido_conteudo(logged_in_page: Page):
    print("[DEBUG] Aguardando área de upload aparecer...")
    logged_in_page.wait_for_selector("span", timeout=5000)

    print("[DEBUG] Tentando fazer upload de um PDF inválido...")
    upload_input = logged_in_page.query_selector('input[type="file"]')
    upload_input.set_input_files(
        "tests/files/invalid_pdf.pdf"
    )  # Este é um PDF "não-laudo"

    print("[DEBUG] Clicando no botão Enviar...")
    logged_in_page.click('button[type="submit"]')

    print("[DEBUG] Aguardando mensagem de erro...")
    logged_in_page.wait_for_selector("div.text-red-500 p", timeout=10000)

    error_message = logged_in_page.text_content("div.text-red-500 p")
    print(f"[DEBUG] Mensagem de erro encontrada: {error_message}")

    assert "Erro" in error_message, (
        f"Mensagem de erro inesperada: {error_message}"
    )
