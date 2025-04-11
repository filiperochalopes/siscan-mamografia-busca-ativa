from playwright.sync_api import Page

def test_upload_arquivo_invalido_mostra_erro(logged_in_page: Page):
    print("[DEBUG] Aguardando área de upload aparecer...")
    logged_in_page.wait_for_selector('span', timeout=5000)

    print("[DEBUG] Tentando fazer upload de um arquivo inválido (.txt)...")
    upload_input = logged_in_page.query_selector('input[type="file"]')
    upload_input.set_input_files('tests/files/example.txt')  # Você deve ter esse arquivo

    print("[DEBUG] Clicando no botão Enviar...")
    logged_in_page.click('button[type="submit"]')

    print("[DEBUG] Aguardando mensagem de erro...")
    logged_in_page.wait_for_selector('div.text-red-500 p', timeout=5000)

    error_message = logged_in_page.text_content('div.text-red-500 p')
    print(f"[DEBUG] Mensagem de erro encontrada: {error_message}")

    assert "Formato de arquivo inválido" in error_message, f"Mensagem de erro inesperada: {error_message}"