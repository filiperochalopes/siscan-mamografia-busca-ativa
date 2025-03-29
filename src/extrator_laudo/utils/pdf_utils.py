import json
import logging
import os
from typing import Optional, List

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PdfUtils:
    @staticmethod
    def save_pages_as_individual(input_pdf_path: str, output_directory: str,
                                 selected_pages: Optional[
                                     List[int]] = None) -> None:
        """
        Salva cada página (ou páginas selecionadas) de um arquivo PDF como arquivos PDF individuais,
        utilizando a biblioteca PyMuPDF (fitz).

        Args:
            input_pdf_path (str): Caminho completo para o arquivo PDF de entrada.
            output_directory (str): Diretório onde os arquivos PDF individuais serão salvos.
            selected_pages (Optional[List[int]]): Lista opcional com os números das páginas (1-based).
                                                  Se None, todas as páginas serão salvas.

        Efeitos colaterais:
            - Cria o diretório de saída, caso não exista.
            - Gera um novo arquivo PDF por página no diretório especificado.

        Exemplo:
            >>> save_pages_as_individual("relatorio.pdf", "./paginas/")
            Página 1 salva em: ./paginas/relatorio_page_1.pdf
        """
        logger.debug(f"Processando arquivo PDF: {input_pdf_path}")
        os.makedirs(output_directory, exist_ok=True)

        doc = fitz.open(input_pdf_path)
        total_pages = len(doc)

        if selected_pages is None:
            page_indices = range(total_pages)
        else:
            page_indices = [p - 1 for p in selected_pages if
                            1 <= p <= total_pages]

        base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]

        for i in page_indices:
            page_number = i + 1  # Para exibição (1-based)

            # Cria um novo documento e insere a página atual
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)

            output_path = os.path.join(output_directory,
                                       f"{base_name}_page_{page_number}.pdf")

            new_doc.save(output_path)
            new_doc.close()

            logger.debug(f"Página {page_number} salva em: {output_path}")

        doc.close()

    @staticmethod
    def extract_and_annotate_first_page(input_pdf: str, output_pdf: str, json_output: str):
        """
        Lê a primeira página de um PDF, extrai as coordenadas de cada palavra
        e salva essas informações em um JSON. Além disso, insere anotações visuais
        no PDF com os valores de x0 e y0 para auxiliar o desenvolvedor a localizar
        visualmente as palavras na página.

        Args:
            input_pdf (str): Caminho para o PDF original.
            output_pdf (str): Caminho onde o novo PDF anotado será salvo.
            json_output (str): Caminho para o arquivo JSON com as coordenadas.

        Raises:
            FileNotFoundError: Se o arquivo PDF não for encontrado.
            ValueError: Se o PDF estiver vazio.
        """
        doc = fitz.open(input_pdf)

        if len(doc) == 0:
            raise ValueError("O PDF está vazio.")

        first_page = doc[0]
        words = first_page.get_text("words")

        # Obtém o menor x0
        min_x0 = min(word[0] for word in words) if words else None

        coordenadas = []

        previous_y0 = 0
        for word in words:
            x0, y0, x1, y1, text, *_ = word

            # Insere anotação visual no PDF (exibe coordenadas x0 e y0)
            first_page.insert_text((x0, y1 + 2), f"{x0:.2f}", fontsize=6,
                                   color=(0, 0, 1))  # azul

            if previous_y0 != y0:
                first_page.insert_text((min_x0 - 20, y1), f"{y0:.2f}",
                                       fontsize=6,
                                       color=(1, 0, 0))  # vermelho
            previous_y0 = y0

            # Salva as coordenadas
            coordenadas.append({
                "texto": text,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1
            })

        # Salva o PDF anotado
        doc.save(output_pdf)
        doc.close()

        # Salva o JSON com as coordenadas
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(coordenadas, f, indent=4, ensure_ascii=False)

        logger.info(f"PDF anotado salvo em: {output_pdf}")
        logger.info(f"Coordenadas salvas em: {json_output}")

    # @staticmethod
    # def extract_and_annotate_first_page(input_pdf: str, output_pdf: str, json_output: str):
    #     """
    #     Lê a primeira página de um PDF, extrai as coordenadas de cada palavra
    #     e salva essas informações em um JSON. Além disso, insere anotações
    #     visuais no PDF com os valores de x0 (ou x0, y0) para auxiliar o
    #     desenvolvedor a localizar visualmente as palavras na página.
    #
    #     Somente a primeira página é salva no novo PDF.
    #
    #     Args:
    #         input_pdf (str): Caminho para o PDF original.
    #         output_pdf (str): Caminho onde o novo PDF (com a primeira página
    #                           anotada) será salvo.
    #         json_output (str): Caminho para o arquivo JSON com as coordenadas.
    #
    #     Raises:
    #         FileNotFoundError: Se o arquivo PDF não for encontrado.
    #         ValueError: Se o PDF estiver vazio.
    #     """
    #     doc = fitz.open(input_pdf)
    #
    #     if len(doc) == 0:
    #         raise ValueError("O PDF está vazio.")
    #
    #     # Copia somente a primeira página para um novo documento
    #     new_doc = fitz.open()
    #     first_page = doc[0]
    #     new_page = new_doc.new_page(width=first_page.rect.width,
    #                                 height=first_page.rect.height)
    #     # renderiza a página 0 do doc original na nova página
    #     new_page.show_pdf_page(first_page.rect, doc, 0)
    #
    #     # Extrai as palavras da página original (não da cópia)
    #     words = first_page.get_text("words")
    #     coordenadas = []
    #
    #     for word in words:
    #         x0, y0, x1, y1, text, *_ = word
    #
    #         # Insere anotação visual no novo PDF
    #         new_page.insert_text((x0, y1 + 2), f"{x0:.2f}", fontsize=6,
    #                              color=(0, 0, 1))  # azul
    #         new_page.insert_text((x0, y0 - 8), f"{y0:.1f}", fontsize=6,
    #                              color=(1, 0, 0))  # vermelho
    #
    #         coordenadas.append({
    #             "texto": text,
    #             "x0": x0,
    #             "y0": y0,
    #             "x1": x1,
    #             "y1": y1
    #         })
    #
    #     new_doc.save(output_pdf)
    #     new_doc.close()
    #     doc.close()
    #
    #     # Salva o JSON com as coordenadas
    #     with open(json_output, 'w', encoding='utf-8') as f:
    #         json.dump(coordenadas, f, indent=4, ensure_ascii=False)
    #
    #     logger.info(
    #         f"PDF anotado salvo (apenas a primeira página) em: {output_pdf}")
    #     logger.info(f"Coordenadas salvas em: {json_output}")

    @staticmethod
    def is_pdf_file(filepath: str) -> bool:
        """
        Verifica se um arquivo é um PDF válido com base na extensão e no
        conteúdo inicial.

        Args:
            filepath (str): Caminho do arquivo a ser verificado.

        Returns:
            bool: True se for um PDF válido, False caso contrário.
        """
        if not filepath.lower().endswith(".pdf"):
            return False

        try:
            with open(filepath, 'rb') as f:
                header = f.read(5)
                return header == b'%PDF-'
        except Exception:
            return False

    @staticmethod
    def is_pdf_openable(filepath: str) -> bool:
        try:
            with fitz.open(filepath):
                return True
        except fitz.FileDataError:
            return False