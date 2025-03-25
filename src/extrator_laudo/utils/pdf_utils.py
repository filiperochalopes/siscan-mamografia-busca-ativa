import json
import os
import logging
from typing import Optional, List
from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PdfUtils:
    @staticmethod
    def save_pages_as_individual(input_pdf_path: str, output_directory: str,
                                 selected_pages: Optional[List[int]] = None):
        """
        Salva cada página de um arquivo PDF como um novo arquivo PDF individual.

        Args:
            input_pdf_path (str): Caminho completo para o arquivo PDF de entrada.
            output_directory (str): Diretório onde os arquivos PDF individuais serão salvos.

        Efeitos colaterais:
            - Cria o diretório de saída, caso não exista.
            - Gera um novo arquivo PDF por página no diretório especificado.

        Exemplo:
            >>> save_pages_as_individual_pdfs("relatorio.pdf", "./paginas/")
            Página 1 salva em: ./paginas/relatorio_page_1.pdf
        """
        logger.debug(f"Processando arquivo PDF: {input_pdf_path}")
        os.makedirs(output_directory, exist_ok=True)

        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)

        # Ajusta lista de páginas para índices baseados em zero
        if selected_pages is None:
            page_indices = range(total_pages)
        else:
            # Subtrai 1 para ajustar do padrão humano (1-based) para
            # índice Python (0-based)
            page_indices = [p - 1 for p in selected_pages if
                            1 <= p <= total_pages]

        for i in page_indices:
            page_number = i + 1  # para exibição no log (1-based)

            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
            output_path = os.path.join(output_directory,
                                       f"{base_name}_page_{page_number}.pdf")

            with open(output_path, 'wb') as f:
                logger.debug(f"Salvando página {page_number} em: {output_path}")
                writer.write(f)

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

        coordenadas = []

        for word in words:
            x0, y0, x1, y1, text, *_ = word

            # Insere anotação visual no PDF (exibe coordenadas x0 e y0)
            first_page.insert_text((x0, y1 + 2), f"{x0:.1f}", fontsize=6,
                                   color=(1, 0, 0))  # vermelho


            # anotacao = f"x0={x0:.1f}, y0={y0:.1f}"
            # first_page.insert_text((x0, y0 - 8), anotacao, fontsize=5, color=(0, 0, 1))  # azul

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

    @staticmethod
    def extract_and_annotate_first_page(input_pdf: str, output_pdf: str, json_output: str):
        """
        Lê a primeira página de um PDF, extrai as coordenadas de cada palavra
        e salva essas informações em um JSON. Além disso, insere anotações
        visuais no PDF com os valores de x0 (ou x0, y0) para auxiliar o
        desenvolvedor a localizar visualmente as palavras na página.

        Somente a primeira página é salva no novo PDF.

        Args:
            input_pdf (str): Caminho para o PDF original.
            output_pdf (str): Caminho onde o novo PDF (com a primeira página
                              anotada) será salvo.
            json_output (str): Caminho para o arquivo JSON com as coordenadas.

        Raises:
            FileNotFoundError: Se o arquivo PDF não for encontrado.
            ValueError: Se o PDF estiver vazio.
        """
        doc = fitz.open(input_pdf)

        if len(doc) == 0:
            raise ValueError("O PDF está vazio.")

        # Copia somente a primeira página para um novo documento
        new_doc = fitz.open()
        first_page = doc[0]
        new_page = new_doc.new_page(width=first_page.rect.width,
                                    height=first_page.rect.height)
        # renderiza a página 0 do doc original na nova página
        new_page.show_pdf_page(first_page.rect, doc, 0)

        # Extrai as palavras da página original (não da cópia)
        words = first_page.get_text("words")
        coordenadas = []

        for word in words:
            x0, y0, x1, y1, text, *_ = word

            # Insere anotação visual no novo PDF
            new_page.insert_text((x0, y1 + 2), f"{x0:.2f}", fontsize=6,
                                 color=(0, 0, 1))  # azul
            # new_page.insert_text((x0, y0 - 8), f"{y0:.1f}", fontsize=6,
            #                      color=(1, 0, 0))  # vermelho

            coordenadas.append({
                "texto": text,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1
            })

        new_doc.save(output_pdf)
        new_doc.close()
        doc.close()

        # Salva o JSON com as coordenadas
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(coordenadas, f, indent=4, ensure_ascii=False)

        logger.info(
            f"PDF anotado salvo (apenas a primeira página) em: {output_pdf}")
        logger.info(f"Coordenadas salvas em: {json_output}")