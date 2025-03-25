import json
import logging
import os
import time
from pathlib import Path
import pandas as pd
import unittest
from src.extrator_laudo.mamografia import SiscanReportMammographyExtract

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
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
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

        base_dir = Path(__file__).resolve().parent
        diretorio_dos_pdf = os.path.join(base_dir, "laudos")

        diretorio_dos_resultados = os.path.join(base_dir, "resultado")
        os.makedirs(diretorio_dos_resultados, exist_ok=True)

        # caminho_txt = os.path.join(base_dir, 'resultado',
        #                            'resultado_laudos.txt')

        inicio = time.time()

        extrator = SiscanReportMammographyExtract(diretorio_dos_pdf,
                                                  diretorio_dos_resultados)
        all_pages_pending_lines, df = extrator.process(
            selected_pages=[84, 96, 129, 221])

        caminho_excel = os.path.join(diretorio_dos_resultados,
                                     'resultado_laudos.xlsx')
        extrator.save_to_excel(caminho_excel)

        fim = time.time()
        print(f"Tempo de execução: {fim - inicio:.4f} segundos")

        print(json.dumps(all_pages_pending_lines, indent=4, ensure_ascii=False))

        df.head()

    def test_extrair_metadados(self):
        base_dir = Path(__file__).resolve().parent
        path_laudo = os.path.join(base_dir, "laudos", "detalheRelatorioLaudos (42).pdf")

        SiscanReportMammographyExtract.gerar_amostra_com_coordenadas(path_laudo)





