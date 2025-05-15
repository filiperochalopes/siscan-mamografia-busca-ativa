import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Tuple, Set

import fitz
import pandas as pd

from src.extrator_laudo.exceptions import EmptyDocumentError
from src.extrator_laudo.utils.file_operator import FileOperator
from src.extrator_laudo.utils.pdf_utils import PdfUtils
from src.extrator_laudo.utils.text_utils import TextUtils

logger = logging.getLogger(__name__)


class SiscanReportExtractor(ABC):
    """
    Classe abstrata para extrair informações de laudos do SISCAN (Sistema de Informação do Câncer)
    a partir de arquivos PDF. Implementações concretas devem fornecer definições específicas
    para seções do documento e lógica personalizada de processamento.
    """

    def __init__(self, input_directory_path_report: str,
                 result_output_directory: str):
        self._input_directory_path_report = input_directory_path_report
        self._result_output_directory = result_output_directory
        self._df = None

    @property
    def df(self) -> pd.DataFrame:
        """
        Retorna o DataFrame contendo os dados extraídos do PDF.

        Returns:
            pd.DataFrame: DataFrame com os dados extraídos.
        """
        if self._df is None:
            raise RuntimeError("Método `process` deve ser chamado antes de "
                               "acessar o DataFrame.")
        return self._df

    @property
    def _text_output(self) -> str:
        """
        Retorna o caminho completo do arquivo com o texto extraído do pdf.

        Returns:
            str: Caminho completo do arquivo texto de destino.
        """
        return os.path.join(self._result_output_directory,
                            "resultado_extracao.txt")

    @abstractmethod
    def get_sections_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna o dicionário contendo todas as seções esperadas no laudo,
        incluindo os campos principais, subseções e coordenadas opcionais
        associadas a cada seção.

        Returns:
            Dict[str, Dict[str, Any]]: Dicionário onde cada chave é o nome de
            uma seção do laudo e o valor é um dicionário com:
                - 'fields': lista de campos esperados na seção. Se Vazio, irá
                            extrair os campos no padrão 'campo: valor'.
                - 'subsections': lista de rótulos de subseções (se houver). Se
                                 vazio, irá extrair subseções no padrão
                                 'subseção:'.
                - 'subsections_coordinate_x0': posição horizontal de referência
                  da subseção. Se None, a subseção será extraída se estiver no
                  padrão 'subseção:'.
        """
        pass

    @abstractmethod
    def get_fields(self) -> Dict[Optional[str], List[str]]:
        """
        Retorna um dicionário contendo os rótulos (labels) que devem ser
        procurados *diretamente nas linhas* de cada seção do laudo para extração
        de valores.

        A identificação desses rótulos durante a extração é desafiadora devido
        à ausência de padrões de formatação consistentes. Isso se manifesta de
        diversas formas: campos sem delimitadores claros, como 'Telefone' (que
        não termina com ':'), rótulos fora de seções nomeadas ('Emissão:',
        'Hora:', etc.) e campos compostos por múltiplas palavras que sucedem
        outros campos na mesma linha, como 'Data da liberação do resultado'.
        Por exemplo, em uma linha como "Conselho: CRM-999 CNS: 999999999999999
        Data da liberação do resultado: 24/01/2023", o sistema não consegue
        discernir que 'Data da liberação do resultado' constitui um campo único.

        As chaves do dicionário representam os nomes das seções (ou None para
        cabeçalho geral fora de seções nominais) e os valores são listas de
        rótulos associados.

        Returns:
            Dict[Optional[str], List[str]]: Mapeamento entre seções e os rótulos
            esperados para extração direta de valores estruturados.
        """
        pass

    @abstractmethod
    def get_ignore_lines(self) -> List[str]:
        """
        Método abstrato para retornar uma lista de linhas que devem ser
        ignoradas durante a extração.

        Returns:
            List[str]: Lista de strings contendo as linhas a serem ignoradas.
        """
        pass

    def save_to_excel(self, filepath: str,
                      columns: Optional[List[str]] = None) -> None:
        """
        Salva os dados extraídos em um arquivo Excel. Se uma lista de colunas for especificada,
        apenas essas colunas serão exportadas. Caso alguma coluna esteja ausente, uma exceção será lançada.

        Args:
            filepath (str): Caminho completo do arquivo Excel a ser salvo.
            columns (Optional[List[str]]): Lista de colunas a serem exportadas. Se None, todas serão salvas.

        Raises:
            EmptyDocumentError: Se o DataFrame estiver vazio.
            ValueError: Se uma ou mais colunas especificadas não existirem no DataFrame.
            IOError: Se houver erro ao salvar o arquivo Excel.
        """
        if self.df.empty:
            raise EmptyDocumentError("Nenhum dado extraído para salvar.")

        df_to_save = self.df

        if columns is not None:
            missing = [col for col in columns if col not in self.df.columns]
            if missing:
                raise ValueError(
                    f"As seguintes colunas não existem no DataFrame extraído: {missing}")
            df_to_save = self.df[columns]

        logger.info(f"Salvando resultados em {filepath}...")
        df_to_save.to_excel(filepath, index=False)

    def _save_to_text(self, text_extra: str, lines: List[str]) -> None:
        """
        Salva os dados extraídos em um arquivo texto.

        Args:
            text_extra (str): Texto extra a ser adicionado ao início do arquivo.
            lines (List[str]): Lista de strings contendo as linhas a serem
                               salvas.

        Raises:
            FileNotFoundError: Se o arquivo de texto não for encontrado.
            IOError: Se houver erro ao salvar o arquivo texto.
        """
        if not lines:
            raise EmptyDocumentError("Nenhum dado extraído para salvar.")

        logger.info(
            f"Salvando resultados em {self._text_output}...")
        FileOperator.salve_text_file(self._text_output,
                                     lines, text_extra)

    @classmethod
    def to_json(cls, df: pd.DataFrame, filepath: str) -> None:
        # Exporta o DataFrame em formato JSON estruturado
        df.to_json(
            filepath,
            orient="records",
            force_ascii=False,
            indent=2,
            date_format="iso"  # Exporta datas como 'YYYY-MM-DD' sem escapar
        )

    def _extract_value(self, label: str, texto: str) -> Optional[str]:
        """
        Extrai o valor associado a um rótulo dentro do texto.

        A função primeiro procura por 'label: valor' na mesma linha. Se o valor 
        capturado parecer ser outro rótulo (termina com ':' ou é 
        todo em maiúsculas), tenta buscar na linha seguinte.

        Args:
            label (str): O rótulo que se deseja extrair.
            texto (str): O texto onde a busca será realizada.

        Returns:
            Optional[str]: O valor associado ao rótulo ou None se não encontrado.
        """
        # Padrão: valor na mesma linha
        pattern_same_line = re.compile(re.escape(label) + r":\s*(.+)")
        match = pattern_same_line.search(texto)
        if match:
            valor = match.group(1).splitlines()[0].strip()
            # Se o valor parecer ser um rótulo (ex.: 'NOME:' 
            # ou somente letras maiúsculas com ':')
            if re.match(r'^[A-ZÀ-Ú0-9\s]+:$', valor):
                match = None
            else:
                return valor

        # Padrão: valor na linha imediatamente após o rótulo
        pattern_next_line = re.compile(re.escape(label) + r":\s*\n\s*(.+)")
        match = pattern_next_line.search(texto)
        if match:
            valor = match.group(1).splitlines()[0].strip()
            return valor
        return None

    def _extract_lines_from_page(
            self, page: fitz.Page,
            y_tolerance: int = 3) -> List[Tuple[str, float]]:
        """
        Reconstrói o texto de uma página do PDF utilizando PyMuPDF (fitz),
        agrupando palavras próximas verticalmente para formar linhas completas.

        Essa função é útil para reorganizar visualmente o texto da página,
        respeitando a estrutura de linhas, baseada na posição vertical (y) das
        palavras.

        Args:
            page (fitz.Page): Página do PDF a ser processada (PyMuPDF).
            y_tolerance (int): Tolerância vertical para agrupar palavras na
                               mesma linha.

        Returns:
            List[str]: Lista de strings representando as linhas reconstruídas
                       do PDF.
        """
        words_raw = page.get_text(
            "words")  # [(x0, y0, x1, y1, text, block, line, word), ...]

        if not words_raw:
            raise EmptyDocumentError("Nenhuma palavra extraída da página.")

        # Converte para dicionários com campos nomeados, para compatibilidade
        # com a estrutura original
        words = [
            {
                "x0": w[0],
                "y0": w[1],
                "x1": w[2],
                "y1": w[3],
                "text": w[4],
            }
            for w in words_raw
        ]

        # Ordena por posição vertical (y0) e horizontal (x0)
        words = sorted(words, key=lambda w: (w['y0'], w['x0']))

        lines = []
        current_line = []
        current_y = None

        for word in words:
            if current_y is None:
                current_y = word['y0']
                current_line.append(word)
            else:
                if abs(word['y0'] - current_y) <= y_tolerance:
                    current_line.append(word)
                else:
                    line_text = " ".join(
                        [w['text'] for w in sorted(current_line,
                                                   key=lambda w: w['x0'])]
                        )
                    lines.append((line_text, current_line[0]['x0'],
                                  current_line[0]['y0']))

                    logger.debug(f"Nova linha: {line_text}")
                    for w in sorted(current_line, key=lambda w: w['x0']):
                        logger.debug(f"  - {w['text']} ({w['x0']}, {w['y0']})")

                    current_line = [word]
                    current_y = word['y0']

        if current_line:
            line_text = " ".join([w['text'] for w in
                                  sorted(current_line, key=lambda w: w['x0'])])
            lines.append((line_text, current_line[0]['x0'],
                          current_line[0]['y0']))

        return lines

    def _extract_labeled_field(self,
                               fields_dict: Dict[Optional[str], List[str]],
                               section_name: str,
                               section_name_key: str,
                               clean_line: str,
                               extracted_lines: Set[str],
                               data: Dict[str, str]) -> str:
        """
        Tenta extrair um valor associado a um rótulo (label) conhecido dentro
        de uma linha de texto, considerando a seção atual do laudo.

        A função verifica se há rótulos definidos para a seção (`section_name`)
        no dicionário `fields_dict`. Para cada rótulo presente, tenta extrair
        o valor correspondente utilizando a função `TextUtils.get_text_after_word`.

        Em caso de sucesso:
          - A linha original (`line`) é adicionada à lista `extracted_lines`.
          - O valor extraído é registrado no dicionário `data`, com a chave
            composta por `section_name_key` e o nome do campo normalizado.
          - O valor e o rótulo são removidos da `clean_line` para evitar duplicações.
          - O campo (rótulo) é removido de `fields_dict[section_name]`.
          - A iteração é interrompida ao encontrar a primeira correspondência.

        Args:
            fields_dict (Dict[Optional[str], List[str]]): Dicionário com os rótulos
                esperados por seção.
            section_name (str): Nome da seção atual em processamento.
            section_name_key (str): Prefixo normalizado do nome da seção, usado como
                parte da chave no dicionário `data`.
            clean_line (str): Linha original extraída do PDF aplicada o strip().
            extracted_lines (List[str]): Lista das linhas que já foram processadas.
            data (Dict[str, str]): Dicionário acumulando os dados extraídos.

        Returns:
            str: A linha limpa (`clean_line`), possivelmente com o rótulo e o valor removidos.
        """
        if fields_dict.get(section_name):
            data_extracted = TextUtils.get_text_after_words(
                clean_line, fields_dict[section_name])
            logger.debug(f"Data extracted: {data_extracted}")
            if data_extracted:
                extracted_lines.add(clean_line)
                for field, value in data_extracted.items():
                    if value and ":" in value:
                        # Se o valor contém ':' (ex.: 'Data da solicitação:
                        # 05/01/2023 UF: PR Município: CURITIBA'), significa que
                        # a linha possui mais de um campo. Nesse caso, usa a função
                        # `extract_key_value_pairs` que extrai todos os campos
                        data_extracted = TextUtils.extract_key_value_pairs(
                            clean_line)
                        # Obtem o primeiro valor do dicionário
                        new_value = next(iter(data_extracted.values()))
                        logger.warning(f"Caracter ':' encontrado no valor: "
                                     f"'{value}'. Novo valor extraído: "
                                     f"'{new_value}'.")
                        value = new_value

                    data[f"{section_name_key}{TextUtils.normalize(field)}"] = (
                        value
                    )
                    if value:
                        clean_line = clean_line.replace(value, "").strip()
                    # Tenta remover o rótulo concatenado com  ':' se houver.
                    # Se ocorrer erro, remove o rótulo sem ':'.
                    try:
                        fields_dict[section_name].remove(f"{field}:")
                        clean_line = clean_line.replace(f"{field}:", "").strip()
                    except ValueError:
                        fields_dict[section_name].remove(field)
                        clean_line = clean_line.replace(field, "").strip()
        return clean_line

    def _process_report(
            self, filename_path: str,
            selected_pages: Optional[List[int]] = None
    ) -> Tuple[Dict[str, List[str]], pd.DataFrame]:
        """
        Processa um laudo de mamografia em formato PDF, extrai informações 
        estruturadas e identifica linhas não processadas, utilizando PyMuPDF.

        O método pode processar todas as páginas do PDF ou apenas páginas
        específicas, conforme a lista fornecida pelo parâmetro `selected_pages`.
        Para cada página processada, o método reconstrói o layout textual,
        identifica seções, extrai campos estruturados e armazena os dados em um
        DataFrame.

        Args:
            filename_path (str): Caminho completo do arquivo PDF a ser processado.
            selected_pages (Optional[List[int]]): Lista de números de páginas a
                                                  serem processadas (1-based).
                                                  Se None, todas as páginas do
                                                  PDF serão processadas.

        Returns:
            Tuple[Dict[str, List[str]], pd.DataFrame]:
                - Um dicionário onde as chaves representam os números das
                  páginas do PDF, e os valores são listas contendo as linhas
                  que não  puderam ser processadas.
                - Um DataFrame contendo os dados estruturados extraídos do
                  laudo.
        """
        sections_all = self.get_sections_all()
        pages_data = []
        pages_pending_lines: Dict[str, List[str]] = {}
        extracted_lines = set()

        logger.info(f"Processando PDF {filename_path}...")

        doc = fitz.open(filename_path)
        total_pages = len(doc)

        if selected_pages is None:
            page_indices = range(total_pages)
        else:
            page_indices = [p - 1 for p in selected_pages if
                            1 <= p <= total_pages]

        for i in page_indices:
            page = doc[i]
            data = {}
            page_number = i + 1  # para exibição no log (1-based)

            logger.info(f"Processando página {page_number}...")

            # Extrai as linhas da página utilizando PyMuPDF
            lines = self._extract_lines_from_page(page, y_tolerance=3)
            self._save_to_text(filename_path, [l[0] for l in lines])

            fields_dict = self.get_fields()
            section = {}
            section_name = None
            section_name_key = ""
            subsection_name = None
            extract_key_value = False

            reading_multiple_lines_content = False

            previous_y0 = lines[0][-1]
            for line, x0, y0 in lines:
                data_extracted = None

                logger.debug(f"> Lendo Linha [{x0:.2f}, {y0:.2f} diff {(y0-previous_y0):.2f}]: {line}")
                clean_line = line.strip()

                if clean_line in self.get_ignore_lines():
                    extracted_lines.add(line)
                    previous_y0 = y0
                    continue

                if clean_line in sections_all.keys():
                    extracted_lines.add(line)
                    section_name = clean_line
                    logger.debug(f"*** Seção identificada: {section_name} ***")
                    section_name_key = f"{TextUtils.normalize(section_name)}__"
                    previous_y0 = y0
                    reading_multiple_lines_content = False
                    continue

                # Extrai campos definidos em 'fields_dict' diretamente da linha,
                # independentemente da seção atual, no caso None.

                if fields_dict.get(None):
                    clean_line = self._extract_labeled_field(
                        fields_dict, None, "geral__",
                        clean_line, extracted_lines, data)
                    # Se a linha foi totalmente processada, pula para a próxima
                    if not clean_line:
                        previous_y0 = y0
                        continue

                if fields_dict.get(section_name):
                    # extrai campos definidos em 'fields_dict' diretamente da
                    # linha da seção atual
                    clean_line = self._extract_labeled_field(
                        fields_dict, section_name, section_name_key,
                        clean_line, extracted_lines, data)

                if section_name:
                    is_subsection = False
                    subsections_coordinate_x0 = sections_all.get(
                        section_name).get('subsections_coordinate_x0')
                    if (subsections_coordinate_x0
                            and subsections_coordinate_x0 == x0):
                        is_subsection = True

                    # Se foi especificado campos em 'fields' de 'sections_all'
                    # da seção atual, extrai da linha atual esses campos e
                    # seus respectivos valores.
                    sections_fields = sections_all.get(section_name).get(
                        'fields', [])
                    if sections_fields:
                        logger.debug(f"Campos especificados {sections_fields} "
                                     f"para a seção {section_name}. "
                                     f"Extraindo-os da linha atual.")
                        data_extracted = TextUtils.get_text_after_words(
                            clean_line, sections_fields)

                    # Se o dicionário 'data_extracted' estiver vazio, tenta
                    # extrair os campos e valores seguindo o padrão
                    # 'rótulo:valor´.
                    if not data_extracted and not is_subsection:
                        data_extracted = TextUtils.extract_key_value_pairs(
                            clean_line)

                    # dicionário 'data_extracted' possui os campos e seus
                    # respectivos valores extraídos da linha atual.
                    # Se 'reading_multiple_lines_content' for True, significa
                    # que está lendo valores de um campo com múltiplas linhas.
                    # Nesse caso, ignora extração do padrão 'rótulo:valor'
                    if not reading_multiple_lines_content and data_extracted:
                        logger.debug(f"Data extracted: {data_extracted}")
                        extract_key_value = True
                        extracted_lines.add(line)
                        for key, value in data_extracted.items():
                            data[
                                f"{section_name_key}{TextUtils.normalize(key)}"] = value
                        previous_y0 = y0
                        continue
                    else:
                        if is_subsection:
                            # if (y0 - previous_y0) > 20.0:
                            if not ":" in clean_line:
                                # Nova subseção.
                                subsection_name = clean_line
                                reading_multiple_lines_content = False

                                # reinicia 'section_name_key' para o nome da
                                # seção
                                section_name_key = f"{TextUtils.normalize(section_name)}__"
                            else:

                                # reinicia 'section_name_key' para o nome da
                                # subseção.
                                section_name_key = (
                                    f"{TextUtils.normalize(section_name)}__"
                                    f"{TextUtils.normalize(subsection_name)}__"
                                )

                            # removendo o caracter ":" de 'clean_line'
                            clean_line = clean_line.replace(":", "")

                        extracted_lines.add(line)
                        if not extract_key_value and not is_subsection:
                            section_name_key = section_name_key.rstrip("_")
                            logger.debug(f"Extraindo valor para {section_name_key}")
                            if data.get(section_name_key) is None:
                                data[section_name_key] = clean_line
                            else:
                                reading_multiple_lines_content = True
                                data[section_name_key] += f"; {clean_line}"
                        else:
                            section_name_key = (
                                f"{section_name_key}"
                                f"{TextUtils.normalize(clean_line)}__"
                            )
                            logger.debug(f"Subseção '{subsection_name}' "
                                         f"identificada, ID "
                                         f"{section_name_key}.")
                            extract_key_value = False
                previous_y0 = y0

            pending_lines = set([l[0] for l in lines]) - extracted_lines
            if pending_lines:
                pages_pending_lines[page_number] = list(pending_lines)
                logger.warning(
                    f"Linhas não processadas (página {page_number}): "
                    f"{pending_lines}")

            pages_data.append(data)

        doc.close()

        # Salva o JSON com os dados extraídos, campos e valores
        base_name = os.path.splitext(os.path.basename(filename_path))[0]
        output_path = os.path.join(self._result_output_directory,
                                   f"{base_name}.json")
        logger.debug(f"Salvando json em {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(pages_data, f, indent=4, ensure_ascii=False)

        return pages_pending_lines, pd.DataFrame(pages_data)

    def process(self,
                selected_pages: Optional[List[int]] = None
                ) -> Tuple[Dict[str, List[str]], pd.DataFrame]:
        """
        Processa os laudos de mamografia do SISCAN a partir de arquivos PDF.

        A função percorre os arquivos contidos no diretório de relatórios
        (`self._input_directory_path_report`), processa cada um deles para extrair
        informações relevantes e armazena os resultados em um DataFrame pandas.
        Além disso, renomeia temporariamente um arquivo de texto
        (`self._filepath_destination_text`) durante o processamento e o remove
        ao final.

        O resultado final consiste em um dicionário contendo as linhas
        pendentes de processamento para cada página dos laudos, bem como um
        DataFrame consolidado com todas as informações extraídas.

        Returns:
            Tuple[Dict[str, List[str]], pd.DataFrame]:
                - Um dicionário onde as chaves são os nomes dos arquivos
                  processados e os valores são listas de strings contendo as
                  linhas pendentes de cada página.
                - Um DataFrame contendo os dados extraídos dos laudos de
                  mamografia.

        Side Effects:
            - Renomeia temporariamente o arquivo
              `self._filepath_destination_text`.
            - Lê e processa os arquivos do diretório `self._input_directory_path_report`.
            - Salva os dados extraídos em um arquivo Excel
              (`self._filepath_destination_spreadsheet`).
            - Remove o arquivo temporário após o processamento.

        Raises:
            FileNotFoundError: Se algum dos arquivos necessários não for
                               encontrado.
            IOError: Se houver erro ao manipular arquivos ou ao salvar o
                     DataFrame.
        """

        # Renomeia temporariamente o arquivo de texto antes do processamento
        FileOperator.rename_file(
            self._text_output,
            f"{self._text_output}_tmp"
        )

        all_df = pd.DataFrame()
        all_pages_pending_lines = {}

        # Percorre os arquivos do diretório de relatórios
        for filename in os.listdir(self._input_directory_path_report):
            filename_path = os.path.join(self._input_directory_path_report,
                                         filename)

            if not PdfUtils.is_pdf_file(filename_path):
                logger.warning(f"Arquivo não é um pdf Válido: {filename_path}. Ignorando.")
                continue

            output_directory = os.path.join(self._result_output_directory,
                                            "pages")
            PdfUtils.save_pages_as_individual(
                filename_path, output_directory, selected_pages)

            # Processa o arquivo atual e obtém as linhas pendentes e o
            # DataFrame correspondente
            pages_pending_lines, df = self._process_report(filename_path,
                                                           selected_pages)
            if df.empty:
                logger.warning(f"Arquivo vazio: {filename_path}, ignorando.")
                continue

            df["file"] = filename  # Adiciona o nome do arquivo como uma nova
            # coluna no DataFrame

            # Armazena os resultados no dicionário e no DataFrame consolidado
            all_pages_pending_lines[filename] = pages_pending_lines
            all_df = pd.concat([all_df, df], ignore_index=True)

        self._df = all_df  # Atualiza o atributo interno do objeto com o
        # DataFrame consolidado

        logger.info(
            f"Textos extraídos salvo em {self._text_output}")

        # Remove o arquivo temporário criado no início
        FileOperator.remove_file(f"{self._text_output}_tmp")

        # Retorna o dicionário de linhas pendentes e o DataFrame consolidado
        return all_pages_pending_lines, self._df

    @classmethod
    def generate_visual_layout_sample(
            cls, pdf_path: str, output_directory: Optional[str] = None) -> None:
        """
        Lê a primeira página de um PDF, extrai as coordenadas de cada palavra
        e salva essas informações em um JSON. Além disso, insere anotações
        visuais no PDF com os valores de x0 e y0 para auxiliar o desenvolvedor
        a localizar visualmente as palavras na página.

        Esse método é útil para que o desenvolvedor possa visualizar a estrutura
        do layout da primeira página e identificar visualmente as coordenadas
        das seções.

        Args:
            pdf_path (str): Caminho completo para o PDF de entrada.
            output_directory (Optional[str]): Diretório onde os arquivos de
                saída (PDF e JSON) serão salvos. Se None, os arquivos serão
                salvos no mesmo diretório do PDF original.

        Side Effects:
            - Cria arquivos "<nome_arquivo>_anotado.pdf" e
              "<nome_arquivo>_coordenadas.json" no diretório de saída
              especificado.

        Raises:
            FileNotFoundError: Se o arquivo PDF não for encontrado.
            ValueError: Se o PDF estiver vazio ou inválido.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        if output_directory is None:
            output_directory = os.path.join(os.path.dirname(pdf_path), "output")

        os.makedirs(output_directory, exist_ok=True)

        output_pdf = os.path.join(output_directory, f"{base_name}_anotado.pdf")
        output_json = os.path.join(output_directory,
                                   f"{base_name}_coordenadas.json")

        PdfUtils.extract_and_annotate_first_page(
            input_pdf=pdf_path,
            output_pdf=output_pdf,
            json_output=output_json
        )

        logger.info(f"Amostra gerada com sucesso: {output_pdf} e {output_json}")