import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Tuple

import pandas as pd
import pdfplumber

from src.extrator_laudo.exceptions import EmptyDocumentError
from src.extrator_laudo.utils.file_operator import FileOperator
from src.extrator_laudo.utils.text_utils import TextUtils

logger = logging.getLogger(__name__)


class SiscanReportExtractor(ABC):
    """
    Classe abstrata para extrair informações de laudos do SISCAN (Sistema de Informação do Câncer)
    a partir de arquivos PDF. Implementações concretas devem fornecer definições específicas
    para seções do documento e lógica personalizada de processamento.
    """

    def __init__(self, dirpath_report: str, filepath_destination_text:str, filepath_destination_spreadsheet:str):
        self._dirpath_report = dirpath_report
        self._filepath_destination_text = filepath_destination_text
        self._filepath_destination_spreadsheet = filepath_destination_spreadsheet
        self._df = None

    @property
    def df(self) -> pd.DataFrame:
        """
        Retorna o DataFrame contendo os dados extraídos do PDF.

        Returns:
            pd.DataFrame: DataFrame com os dados extraídos.
        """
        return self._df

    @abstractmethod
    def get_sections_all(self) -> List[str]:
        """
        Método abstrato para retornar um dicionário contendo todas as seções esperadas no laudo.

        Returns:
            List[str]: Lista contendo as seções do laudo.
        """
        pass

    @abstractmethod
    def get_fields(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_ignore_lines(self) -> List[str]:
        """
        Método abstrato para retornar uma lista de linhas que devem ser ignoradas durante a extração.

        Returns:
            List[str]: Lista de strings contendo as linhas a serem ignoradas.
        """
        pass

    def _extract_value(self, label: str, texto: str) -> Optional[str]:
        """
        Extrai o valor associado a um rótulo dentro do texto.

        A função primeiro procura por 'label: valor' na mesma linha. Se o valor capturado parecer ser outro
        rótulo (termina com ':' ou é todo em maiúsculas), tenta buscar na linha seguinte.

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
            # Se o valor parecer ser um rótulo (ex.: 'NOME:' ou somente letras maiúsculas com ':')
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

    def _extract_lines_from_page(self, page: pdfplumber.page.Page, y_tolerance: int = 3) -> List[str]:
        """
            Está função em como objetivo reconstruir o texto de uma página do PDF agrupando as palavras que estão
            próximas verticalmente, de forma a recriar as linhas conforme o layout original.

            Extrai todas as palavras da página usando page.extract_words(). Cada palavra vem com metadados:
                - text: O conteúdo textual extraído da palavra.
                - x0: A coordenada x da borda esquerda da caixa delimitadora da palavra.
                - x1: A coordenada x da borda direita da caixa delimitadora da palavra.
                - top: A coordenada y do topo da caixa delimitadora da palavra, normalmente medida a partir do
                        topo da página.
                - doctop: Semelhante a top, mas pode representar a posição vertical relativa ao documento
                            inteiro (útil em casos com múltiplas páginas, por exemplo).
                - bottom: A coordenada y da borda inferior da caixa delimitadora da palavra.
                - upright: Um valor booleano que indica se o texto está “na vertical” (upright = True) – isto é,
                            não está rotacionado.
                - height: A altura da caixa que envolve a palavra (geralmente, bottom - top).
                - width: A largura da caixa que envolve a palavra (geralmente, x1 - x0).
                - direction: A direção do texto. Por exemplo, "ltr" significa left-to-right (da esquerda para
                                a direita). Isso pode ser útil para documentos que contenham texto em direções
                                diferentes.
                ex.:
                    {
                        'text': 'Emissão:', 'x0': 455.0, 'x1': 487.896, 'top': 22.0859999999999,
                        'doctop': 22.0859999999999, 'bottom': 30.0859999999999, 'upright': True,
                        'height': 8.0, 'width': 32.896000000000015, 'direction': 'ltr'
                    }
            Args:
                page (pdfplumber.page.Page): Página do PDF a ser processada.
                y_tolerance (int, optional): Tolerância de proximidade vertical para agrupar palavras em uma mesma linha.
                                            Padrão é 3.

            Returns:
                List[str]: Lista de strings, onde cada string representa uma linha de texto reconstruída do PDF.
        """

        # extrai todas as palavras da página.
        words = page.extract_words()
        if not words:
            raise EmptyDocumentError("Nenhuma palavra extraída da página.")

        # Ordena as palavras pela posição vertical (top) para que palavras na mesma altura fiquem juntas) e, depois
        # pela posição horizontal (x0) para preservar a ordem da esquerda para a direita).
        words = sorted(words, key=lambda w: (w['top'], w['x0']))

        lines = []  # armazenar o resultado final, ou seja, as linhas de texto
        current_line = [] # armazenar as palavras que pertencem à linha que está sendo construída
        current_y = None # guarda a posição vertical de referência para a linha atual

        for word in words:
            if current_y is None: # se None, significa que é a primeira palavra
                current_y = word['top']
                current_line.append(word) # a palavra é adicionada.
            else:
                # Palavras subsequentes:
                # Se a palavra estiver próxima da linha atual, adiciona à mesma linha
                # verifica-se se a diferença entre a posição vertical da nova palavra e 'current_y' é menor ou igual
                # a 'y_tolerance' (tolerância vertical).
                if abs(word['top'] - current_y) <= y_tolerance:
                    current_line.append(word)
                else:
                    # diferença é maior, isso indica que a nova palavra está em uma linha diferente. Nesse caso, as
                    # palavras acumuladas em 'current_line' são ordenadas pela posição horizontal (para manter a ordem
                    # da esquerda para a direita) e concatenadas em uma única string, que representa a linha completa.
                    line_text = " ".join([w['text'] for w in sorted(current_line, key=lambda w: w['x0'])])
                    lines.append(line_text)

                    # Reinicia para uma nova linha
                    current_line = [word] # reinicia com a palavra atual
                    current_y = word['top'] # atualiza para a posição vertical da palavra atual

        if current_line:
            # existe palara acumulada, ou seja, a última linha da página. Essa linha é finalizada da mesma forma,
            #isto é, ordenando as palavras e juntando-as em uma string e adicionada à lista lines.
            line_text = " ".join([w['text'] for w in sorted(current_line, key=lambda w: w['x0'])])
            lines.append(line_text)

        return lines

    def _process_report(self, filename_path: str) -> Tuple[Dict[str, List[str]], pd.DataFrame]:
        """
        Processa um laudo de mamografia em formato PDF, extrai informações estruturadas e identifica
        linhas não processadas.

        O método percorre todas as páginas do arquivo PDF, reconstrói o layout original do texto e
        identifica seções e campos estruturados dentro do documento. Os valores extraídos são armazenados
        em um dicionário, que posteriormente é convertido em um DataFrame pandas. Além disso, as linhas
        que não puderam ser processadas são registradas separadamente.

        Args:
            filename_path (str): Caminho completo do arquivo PDF a ser processado.

        Returns:
            Tuple[Dict[str, List[str]], pd.DataFrame]:
                - Um dicionário onde as chaves representam os números das páginas do PDF, e os valores são
                listas contendo as linhas que não puderam ser processadas.
                - Um DataFrame contendo os dados estruturados extraídos do laudo.

        Side Effects:
            - Lê e processa o conteúdo do PDF especificado.
            - Gera logs informativos e de depuração para acompanhamento do processamento.
            - Armazena as informações extraídas em um DataFrame pandas.

        Raises:
            FileNotFoundError: Se o arquivo PDF não for encontrado no caminho especificado.
            IOError: Se houver erro ao abrir ou ler o arquivo PDF.
            ValueError: Se não for possível processar corretamente o conteúdo do PDF.

        Example:
            >>> processor = ReportProcessor()
            >>> pending_lines, df = processor._process_report("laudo_mamografia.pdf")
            >>> print(df.head())
        """

        # Obtém todas as seções esperadas do laudo
        sections_all = self.get_sections_all()

        # Lista para armazenar os dados extraídos de todas as páginas
        pages_data = []

        # Dicionário onde a chave é o número da página e o valor é uma lista de linhas não processadas
        pages_pending_lines: Dict[str, List[str]] = {}

        # Inicializa contadores auxiliares
        num_page = 0
        extracted_lines = []

        logger.info(f"Processando PDF {filename_path}...")

        # Abre o arquivo PDF e processa cada página
        with pdfplumber.open(filename_path) as pdf:
            for page in pdf.pages:
                data = {}  # Dicionário para armazenar os dados extraídos da página

                num_page += 1
                logger.info(f"Processando página {num_page}...")

                # Extrai todas as linhas da página reconstruindo o layout original
                lines = self._extract_lines_from_page(page, y_tolerance=3)

                FileOperator.salve_text_file(self._filepath_destination_text, lines, filename_path)

                # Obtém os campos esperados dentro das seções
                fields_dict = self.get_fields()

                section = {}  # Armazena os campos da seção atual
                section_name = None  # Nome da seção sendo processada
                section_name_key = ""  # Nome da seção em formato normalizado
                extract_key_value = False  # Flag para indicar se valores foram extraídos

                for line in lines:
                    logger.debug(f"Lendo Linha: {line}")

                    # Remove espaços extras e caracteres ':' da linha
                    clean_line = line.strip()

                    # Verifica se a linha deve ser ignorada (exemplo: cabeçalhos repetitivos)
                    if clean_line in self.get_ignore_lines():
                        extracted_lines.append(line)
                        continue

                    # Verifica se a linha representa uma nova seção do laudo
                    if clean_line in sections_all:
                        extracted_lines.append(line)
                        section_name = clean_line
                        logger.debug(f"*** Seção identificada: {section_name} ***")

                        # Normaliza o nome da seção para ser usado como chave nos dados extraídos
                        section_name_key = f"{TextUtils.normalize(section_name)}__"
                        continue

                    # Se houver um campo esperado dentro da seção, tenta extrair o valor correspondente
                    if fields_dict.get(section_name):
                        for field in fields_dict[section_name]:
                            value = TextUtils.get_text_after_word(clean_line, field)
                            if value:
                                extracted_lines.append(line)
                                data[f"{section_name_key}{TextUtils.normalize(field)}"] = value

                                # Remove o valor e o rótulo extraídos da linha para evitar duplicação
                                clean_line = clean_line.replace(value, "").strip()
                                clean_line = clean_line.replace(field, "").strip()

                                # Remove o campo extraído da lista para evitar processamentos duplicados
                                fields_dict[section_name].remove(field)
                                break

                    # Se uma seção foi identificada, tenta extrair pares chave-valor
                    if section_name:
                        data_extracted = TextUtils.extract_key_value_pairs(clean_line)
                        if data_extracted:
                            extract_key_value = True
                            extracted_lines.append(line)
                            for key, value in data_extracted.items():
                                data[f"{section_name_key}{TextUtils.normalize(key)}"] = value
                            continue
                        else:
                            extracted_lines.append(line)

                            if not extract_key_value:
                                # Remove "__" do final do nome da seção se existir
                                section_name_key = section_name_key.rstrip("_")
                                if data.get(section_name_key) is None:
                                    data[section_name_key] = clean_line
                                else:
                                    data[section_name_key] += f"; {clean_line}"
                            else:
                                # Se não houve extração, adiciona "__" para indicar um possível subcampo
                                section_name_key = f"{TextUtils.normalize(section_name)}__{TextUtils.normalize(clean_line)}__"
                                extract_key_value = False

                # Identifica e registra no log as linhas que não foram processadas
                pending_lines = set(lines) - set(extracted_lines)
                if pending_lines:
                    pages_pending_lines[num_page] = list(pending_lines)
                    logger.warning(f"Linhas não processadas: {pending_lines}")

                # Adiciona os dados extraídos da página à lista de páginas processadas
                pages_data.append(data)

                # Para depuração, processa apenas a primeira página
                break

        # Retorna as linhas não processadas e os dados extraídos em formato DataFrame
        return pages_pending_lines, pd.DataFrame(pages_data)

    def process(self) -> Tuple[Dict[str, List[str]], pd.DataFrame]:
        """
        Processa os laudos de mamografia do SISCAN a partir de arquivos PDF.

        A função percorre os arquivos contidos no diretório de relatórios (`self._dirpath_report`),
        processa cada um deles para extrair informações relevantes e armazena os resultados em um
        DataFrame pandas. Além disso, renomeia temporariamente um arquivo de texto (`self._filepath_destination_text`)
        durante o processamento e o remove ao final.

        O resultado final consiste em um dicionário contendo as linhas pendentes de processamento para
        cada página dos laudos, bem como um DataFrame consolidado com todas as informações extraídas.

        Returns:
            Tuple[Dict[str, List[str]], pd.DataFrame]:
                - Um dicionário onde as chaves são os nomes dos arquivos processados e os valores são listas de strings
                contendo as linhas pendentes de cada página.
                - Um DataFrame contendo os dados extraídos dos laudos de mamografia.

        Side Effects:
            - Renomeia temporariamente o arquivo `self._filepath_destination_text`.
            - Lê e processa os arquivos do diretório `self._dirpath_report`.
            - Salva os dados extraídos em um arquivo Excel (`self._filepath_destination_spreadsheet`).
            - Remove o arquivo temporário após o processamento.

        Raises:
            FileNotFoundError: Se algum dos arquivos necessários não for encontrado.
            IOError: Se houver erro ao manipular arquivos ou ao salvar o DataFrame.
        """

        # Renomeia temporariamente o arquivo de texto antes do processamento
        FileOperator.rename_file(self._filepath_destination_text, f"{self._filepath_destination_text}_tmp")

        all_df = pd.DataFrame()
        all_pages_pending_lines = {}

        # Percorre os arquivos do diretório de relatórios
        for filename in os.listdir(self._dirpath_report):
            filename_path = os.path.join(self._dirpath_report, filename)

            # Processa o arquivo atual e obtém as linhas pendentes e o DataFrame correspondente
            pages_pending_lines, df = self._process_report(filename_path)
            df["file"] = filename  # Adiciona o nome do arquivo como uma nova coluna no DataFrame

            # Armazena os resultados no dicionário e no DataFrame consolidado
            all_pages_pending_lines[filename] = pages_pending_lines
            all_df = pd.concat([all_df, df], ignore_index=True)

            break  # Apenas o primeiro arquivo é processado (comportamento a ser revisado)

        # Salva os dados extraídos em um arquivo Excel
        logger.info(f"Salvando resultados em {self._filepath_destination_spreadsheet}...")
        all_df.to_excel(self._filepath_destination_spreadsheet, index=False)

        logger.info(f"Textos extraídos salvo em {self._filepath_destination_text}")

        self._df = all_df  # Atualiza o atributo interno do objeto com o DataFrame consolidado

        # Remove o arquivo temporário criado no início
        FileOperator.remove_file(f"{self._filepath_destination_text}_tmp")

        # Retorna o dicionário de linhas pendentes e o DataFrame consolidado
        return all_pages_pending_lines, self._df
