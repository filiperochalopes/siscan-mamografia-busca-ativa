import re
import unicodedata
from typing import Dict, List, Optional


class TextUtils:
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normaliza o texto removendo acentos, caracteres especiais e convertendo sequências de espaços para '_'.
        Retorna o texto em letras minúsculas.
        """
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'\s+', '_', text)
        text = re.sub(r'[^a-zA-Z0-9_]', '', text)
        return text.lower()

    @staticmethod
    def get_text_after_word(text: str, word: str) -> str:
        """
        Retorna o texto que vem após a primeira ocorrência da palavra no texto.

        Args:
            text (str): O texto completo.
            word (str): A palavra de referência.

        Returns:
            str: O texto que aparece depois da palavra. Se a palavra não for
            encontrada, retorna uma string vazia.
        """
        index = text.find(word)
        if index == -1:
            return ""
        return text[index + len(word):].strip()

    @staticmethod
    def extract_key_value_pairs(text: str) -> Dict[str, str]:
        """
        Extrai pares chave-valor de um texto no formato "chave: valor", sem
        precisar de uma lista fixa de chaves.

        A função detecta dinamicamente as chaves como qualquer sequência de
        palavras que precede ":".

        Args:
            text (str): Texto contendo pares separados por ":".

        Returns:
            Dict[str, str]: Dicionário onde as chaves são os textos antes de ":"
                            e os valores são os textos depois de ":".
        """
        # Regex para capturar qualquer palavra seguida de ":", extraindo seu
        # valor até encontrar outra chave ou o fim do texto
        pattern = r"(\S.*?):\s*(.*?)(?=\s+\S+?:|$)"

        matches = re.findall(pattern, text)

        return {key.strip(): value.strip() for key, value in matches}

    @staticmethod
    def get_text_after_words(text: str, labels: List[str]) -> Dict[
        str, Optional[str]]:
        """
        Extrai valores a partir de múltiplos rótulos em um texto plano.
        O valor de cada rótulo é considerado como o conteúdo entre ele e o próximo rótulo.

        Args:
            text (str): Texto a ser analisado.
            labels (List[str]): Lista de rótulos com dois-pontos.

        Returns:
            Dict[str, Optional[str]]: Dicionário com os rótulos sem dois-pontos como chave
                                      e os respectivos valores extraídos (ou None).
        """
        result = {}
        positions = []

        # Mapeia posições de início de cada rótulo no texto
        for label in labels:
            match = re.search(re.escape(label), text)
            if match:
                positions.append(
                    (label.rstrip(':'), match.start(), match.end()))

        # Ordena pela posição de início
        positions.sort(key=lambda x: x[1])

        # Percorre os rótulos encontrados e extrai valores até o próximo rótulo
        for i, (key, start, end) in enumerate(positions):
            next_start = positions[i + 1][1] if i + 1 < len(positions) else len(
                text)
            raw_value = text[end:next_start].strip()
            result[key] = raw_value if raw_value else None
        return result