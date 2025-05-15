from __future__ import annotations
from pathlib import Path
import pandas as pd
import shutil
import tempfile
from src.utils.mammography import (
    extrair_birads,
    calcular_idade,
    is_densa,
    verificar_usg,
    definir_alterado,
)
from src.extrator_laudo.mamografia import SiscanReportMammographyExtract
from datetime import datetime
import re
import uuid
import secrets
from openpyxl import load_workbook
from flask import url_for
from src.services.config import Config
from src.utils.validators import is_valid_siscan_df
from werkzeug.datastructures import FileStorage as File

class ReportService:
    def __init__(self, file: File):
        self.file = file
        self.extrator = SiscanReportMammographyExtract("tmp", "tmp")

    def process(self) -> pd.DataFrame:
        _, df = self.extrator.process()
        
        if not is_valid_siscan_df(df):
            raise ValueError("Erro: O arquivo enviado não é um laudo de mamografia SISCAN válido.")
    
        if df.empty or not df["paciente__nome"].any():
            raise ValueError("PDF não contém laudo válido")
        return df

    def build_excel(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        nome_arquivo = f"resultado_processamento_laudos_siscan_{timestamp}.xlsx"
        export_dir = Path("src/static/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        # Cria uma pasta temporária isolada
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_dir = Path(tmpdirname)

            # Salva o arquivo enviado dentro da pasta temporária
            temp_pdf = tmp_dir / "input.pdf"
            tmp_dir.mkdir(exist_ok=True)
            self.file.save(temp_pdf)

            try:
                # Usa a pasta temporária no extrator
                self.extrator = SiscanReportMammographyExtract(str(tmp_dir), str(tmp_dir))
                df = self.process()

            except Exception as e:
                raise ValueError(f"Erro ao processar o PDF: {str(e)}")

            print(df.columns, flush=True)
            print(df.head(), flush=True)

            # Gera uma pasta final para salvar os PDFs processados
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            folder_hash = secrets.token_hex(6)
            folder_name = f"{timestamp}_{folder_hash}"

            static_folder = Path("src/static")
            dest_folder = static_folder / folder_name
            dest_folder.mkdir(parents=True, exist_ok=True)

            token = secrets.token_hex(8)

            # Renomeia os laudos processados
            tmp_pages = tmp_dir / "pages"
            mapping_pdf = {}
            for pdf in tmp_pages.glob("*.pdf"):
                match = re.search(r'_page_(\d+)$', pdf.stem)
                if match:
                    page_number = int(match.group(1))
                    new_name = f"{uuid.uuid4()}.pdf"
                    dest_path = dest_folder / new_name
                    shutil.copy2(pdf, dest_path)  # Copia com metadados
                    pdf.unlink()  # Depois apaga o original
                    mapping_pdf[page_number] = new_name
                else:
                    continue

            # Processa o DataFrame para o Excel
            novo_df = pd.DataFrame()
            novo_df["Nome"] = df["paciente__nome"]
            data_nasc_dt = pd.to_datetime(df["paciente__data_do_nascimento"], format="%d/%m/%Y", errors="coerce")
            novo_df["Idade"] = data_nasc_dt.apply(calcular_idade)
            novo_df["Data de nascimento"] = data_nasc_dt.dt.strftime("%m/%d/%Y")
            novo_df["Nome da mãe"] = df["paciente__mae"]
            novo_df["CNS"] = df["paciente__cartao_sus"]
            novo_df["Data do exame"] = pd.to_datetime(df["geral__emissao"], format="%d/%m/%Y", errors="coerce").dt.strftime("%m/%d/%Y")
            novo_df["Unidade de saúde"] = df["unidade_de_saude__nome"]
            novo_df["CNES"] = df["unidade_de_saude__cnes"]
            novo_df["Tipo do Exame"] = df["resultado_exame__indicacao__tipo_de_mamografia"]

            birads_md = df["resultado_exame__classificacao_radiologica__mama_direita"].apply(lambda x: extrair_birads(str(x)))
            birads_me = df["resultado_exame__classificacao_radiologica__mama_esquerda"].apply(lambda x: extrair_birads(str(x)))

            novo_df["MD - BIRADS"] = birads_md.apply(lambda x: f"BI-RADS {int(x)}" if pd.notna(x) else "")
            novo_df["ME - BIRADS"] = birads_me.apply(lambda x: f"BI-RADS {int(x)}" if pd.notna(x) else "")
            novo_df["MD - Mama densa"] = df["resultado_exame__mama_direita__tipo_de_mama"].apply(is_densa)
            novo_df["ME - Mama densa"] = df["resultado_exame__mama_esquerda__tipo_de_mama"].apply(is_densa)
            novo_df["USG"] = df.apply(verificar_usg, axis=1)
            novo_df["Alterado"] = df.apply(lambda row: definir_alterado(
                row,
                extrair_birads(str(row.get("resultado_exame__classificacao_radiologica__mama_direita", ""))),
                extrair_birads(str(row.get("resultado_exame__classificacao_radiologica__mama_esquerda", ""))),
                verificar_usg(row)
            ), axis=1)

            novo_df["Link para arquivo"] = df["geral__pagina"].apply(
                lambda x: f"{Config.APP_URL}/static/{folder_name}/{mapping_pdf.get(int(x), '')}?token={token}"
                if pd.notna(x) and int(x) in mapping_pdf else ""
            )

            novo_df["Pendente"] = 1
            novo_df["Data de ação"] = pd.NaT
            novo_df["Resultado da ação"] = ""
            novo_df["Observações"] = ""

            colunas_ordenadas = [
                "Nome", "Data de nascimento", "Idade", "Nome da mãe", "CNS",
                "Unidade de saúde", "CNES", "Data do exame", "Tipo do Exame",
                "MD - BIRADS", "MD - Mama densa", "ME - BIRADS", "ME - Mama densa",
                "Alterado", "USG", "Link para arquivo", "Pendente",
                "Data de ação", "Resultado da ação", "Observações"
            ]
            novo_df = novo_df[colunas_ordenadas]

            novo_df.sort_values(
                by=["Alterado", "Tipo do Exame", "CNES", "Unidade de saúde", "Nome"],
                ascending=[False, True, True, True, True],
                inplace=True
            )

            caminho_excel = export_dir / nome_arquivo
            novo_df.to_excel(caminho_excel, index=False)

            wb = load_workbook(caminho_excel)
            ws = wb.active
            link_col_index = colunas_ordenadas.index("Link para arquivo") + 1

            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=link_col_index)
                if cell.value:
                    link = cell.value
                    cell.hyperlink = link
                    cell.value = "Acessar o laudo"
                    cell.style = "Hyperlink"

            wb.save(caminho_excel)

            return url_for('static', filename=f'exports/{nome_arquivo}')