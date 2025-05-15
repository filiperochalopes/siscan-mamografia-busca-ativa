import json
import logging
import os
import time
from pathlib import Path
import pandas as pd
import unittest
from src.extrator_laudo.mamografia import SiscanReportMammographyExtract
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Ajustar opções do Pandas para exibir todas as colunas
pd.set_option("display.max_columns", None)  # Exibe todas as colunas
pd.set_option("display.expand_frame_repr",
              False)  # Não quebra linhas automaticamente


# utilitário nativo de teste
# python -m unittest src.extrator_laudo.tests.test_extrai_lado_mamografia.TestExtrator.test_extrair_laudo


# Com pytest
# pytest src.extrator_laudo.tests.test_extrai_lado_mamografia.TestExtrator.test_extrair_laudo


class TestExtrator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent
        cls.laudos_dir = Path(os.getenv("TEST_FILES_DIR", cls.base_dir / "laudos"))

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s | %(levelname)-8s | %(name)-25s | %(funcName)-25s | %(message)s',
            handlers=[logging.StreamHandler()]
        )

        # Reduz o nível de log para bibliotecas externas
        logging.getLogger('pdfplumber').setLevel(logging.WARNING)
        logging.getLogger('pdfminer').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
        logging.getLogger('pandas').setLevel(logging.WARNING)

    def test_extrair_laudo(self):
        # planilha siscan https://drive.google.com/drive/u/0/folders/1DrZUj9L0BbETvEslezvfprmuDoe2LBDx

        diretorio_dos_resultados = os.path.join(self.laudos_dir, "resultado")
        os.makedirs(diretorio_dos_resultados, exist_ok=True)

        inicio = time.time()

        extrator = SiscanReportMammographyExtract(self.laudos_dir,
                                                  diretorio_dos_resultados)
        all_pages_pending_lines, df = extrator.process(
            selected_pages=[1, 84, 96, 129, 221]) # [1, 84, 96, 129, 221]

        caminho_excel = os.path.join(diretorio_dos_resultados,
                                     'resultado_laudos.xlsx')

        extrator.save_to_excel(caminho_excel, sorted(extrator.df.columns))

        fim = time.time()
        print(f"Tempo de execução: {fim - inicio:.4f} segundos")

        df.head()

    def test_extrair_metadados(self):

        assert self.laudos_dir.exists(), f"Diretório não encontrado: {self.laudos_dir}"
        pdfs = list(self.laudos_dir.glob("*.pdf"))
        assert pdfs, f"Nenhum PDF encontrado em: {self.laudos_dir}"

        for pdf_file in pdfs:
            pdf_file_name = os.path.join(self.laudos_dir, pdf_file.name)
            print(f"[INFO] Gerando visual layout para: {pdf_file_name}")
            SiscanReportMammographyExtract.generate_visual_layout_sample(pdf_file_name)

