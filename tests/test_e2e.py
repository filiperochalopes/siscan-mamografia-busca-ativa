import secrets
from playwright.sync_api import Page
import pandas as pd
from dotenv import load_dotenv
from .conftest import APP_URL, TOKEN

load_dotenv()


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


def test_login_com_token_correto(page: Page):
    print(f"[DEBUG] Acessando {APP_URL}...")
    page.goto(APP_URL)

    print("[DEBUG] Aguardando input de token aparecer...")
    page.wait_for_selector('input[name="token"]', timeout=5000)

    print("[DEBUG] Preenchendo o token correto...")
    page.fill('input[name="token"]', TOKEN)

    print("[DEBUG] Clicando no botão Entrar e aguardando redirecionamento...")
    with page.expect_navigation(timeout=10000):
        page.click('button[type="submit"]')

    print("[DEBUG] Aguardando área de upload aparecer na nova página...")
    page.wait_for_selector("span", timeout=5000)

    print("[DEBUG] Verificando se o texto do span está correto...")
    upload_text = page.text_content("span")
    print(f"[DEBUG] Texto encontrado: {upload_text}")

    assert "Arraste ou clique para selecionar um arquivo" in upload_text, (
        f"Texto inesperado após login: {upload_text}"
    )


def test_upload_pdf_apos_login(page: Page):
    print(f"[DEBUG] Acessando {APP_URL}...")
    page.goto(APP_URL)

    print("[DEBUG] Logando com token correto...")
    page.wait_for_selector('input[name="token"]', timeout=5000)
    page.fill('input[name="token"]', TOKEN)
    page.click('button[type="submit"]')

    print("[DEBUG] Aguardando área de upload aparecer...")
    page.wait_for_selector("span", timeout=5000)

    print("[DEBUG] Realizando upload do arquivo PDF...")
    upload_input = page.query_selector('input[type="file"]')
    upload_input.set_input_files(
        "tests/files/example.pdf"
    )  # Caminho relativo ao seu teste

    print("[DEBUG] Clicando no botão Enviar...")
    page.click('button[type="submit"]')

    print("[DEBUG] Aguardando link de download aparecer...")
    page.wait_for_selector("a.underline.font-semibold", timeout=10000)

    print("[DEBUG] Capturando o link de download...")
    download_link = page.query_selector("a.underline.font-semibold")
    assert download_link.is_visible(), "Link de download não apareceu após upload"

    download_text = download_link.text_content()
    print(f"[DEBUG] Texto do link encontrado: {download_text}")

    assert "clique aqui para baixar o relatório" in download_text.lower(), (
        f"Texto do link inesperado: {download_text}"
    )


def test_upload_pdf_e_validar_xlsx(page: Page, tmp_path):
    print(f"[DEBUG] Acessando {APP_URL}...")
    page.goto(APP_URL)

    print("[DEBUG] Logando com token correto...")
    page.wait_for_selector('input[name="token"]', timeout=5000)
    page.fill('input[name="token"]', TOKEN)

    with page.expect_navigation(timeout=10000):
        page.click('button[type="submit"]')

    print("[DEBUG] Aguardando área de upload aparecer...")
    page.wait_for_selector("span", timeout=5000)

    print("[DEBUG] Realizando upload do arquivo PDF...")
    upload_input = page.query_selector('input[type="file"]')
    upload_input.set_input_files("tests/files/example.pdf")

    # Iniciar o monitoramento de download
    print("[DEBUG] Aguardando evento de download...")
    with page.expect_download() as download_info:
        page.click('button[type="submit"]')

    download = download_info.value

    # Salvar o arquivo baixado em um caminho temporário
    download_path = tmp_path / "resultado_download.xlsx"
    download.save_as(str(download_path))
    print(f"[DEBUG] Arquivo salvo em: {download_path}")

    # Agora vamos abrir o arquivo Excel e validar as colunas
    print("[DEBUG] Lendo o arquivo Excel...")
    df = pd.read_excel(download_path)

    print("[DEBUG] Colunas encontradas:", df.columns.tolist())

    # Validar que certas colunas estão presentes
    expected_columns = [
        "Nome",
        "Data de nascimento",
        "Nome da mãe",
        "CNS",
        "Data do exame",
        "Unidade de saúde",
        "CNES",
        "MD - BIRADS",
        "MD - Mama densa",
        "ME - BIRADS",
        "ME - Mama densa",
        "Alterado",
        "USG",
        "Link para arquivo",
        "Pendente",
        "Data de ação",
        "Resultado da ação",
        "Observações",
    ]  # <-- ajuste para as colunas que você espera
    for col in expected_columns:
        assert col in df.columns, f"Coluna '{col}' não encontrada no arquivo!"


def test_clicar_link_download_arquivo(logged_in_page: Page, tmp_path):
    print("[DEBUG] Aguardando área de upload aparecer...")
    logged_in_page.wait_for_selector('span', timeout=5000)

    print("[DEBUG] Realizando upload do arquivo PDF...")
    upload_input = logged_in_page.query_selector('input[type="file"]')
    upload_input.set_input_files('tests/files/example.pdf')  # Certifique-se que o arquivo existe

    print("[DEBUG] Clicando no botão Enviar...")
    logged_in_page.click('button[type="submit"]')

    print("[DEBUG] Aguardando o link de download aparecer...")
    logged_in_page.wait_for_selector('a.underline.font-semibold', timeout=10000)

    print("[DEBUG] Capturando o link de download...")
    download_link = logged_in_page.query_selector('a.underline.font-semibold')
    assert download_link.is_visible(), "Link de download não visível."

    print("[DEBUG] Clicando no link e aguardando download...")
    with logged_in_page.expect_download() as download_info:
        download_link.click()

    download = download_info.value

    # Salva o arquivo baixado em um caminho temporário
    download_path = tmp_path / "arquivo_baixado_via_link.xlsx"
    download.save_as(str(download_path))

    print(f"[DEBUG] Arquivo baixado e salvo em: {download_path}")

    # Verifica que o arquivo existe e não está vazio
    assert download_path.exists(), "Arquivo baixado não encontrado!"
    assert download_path.stat().st_size > 0, "Arquivo baixado está vazio!"