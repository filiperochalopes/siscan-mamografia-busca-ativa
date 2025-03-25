import logging
import os
from typing import List

logger = logging.getLogger(__name__)


class FileOperator:
    @staticmethod
    def salve_text_file(output_file: str, lines: List[str], text_extra: str):
        # Salvando no arquivo de texto no modo append ("a")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(text_extra + "\n")
            f.write("*****************************************************************\n")
            for line in lines:
                f.write(line + "\n")
            f.write("\n")

    @staticmethod
    def remove_file(file_name: str) -> bool:
        """
        Remove um arquivo se ele existir.

        Args:
            file_name (str): Nome do arquivo a ser removido.

        Returns:
            bool: True se o arquivo foi removido com sucesso, False se o arquivo não existir.
        """
        if os.path.exists(file_name):
            os.remove(file_name)
            logger.debug(f"Arquivo '{file_name}' removido com sucesso.")
            return True
        else:
            logger.warning(f"Aviso: O arquivo '{file_name}' não foi encontrado.")
            return False

    @staticmethod
    def rename_file(old_name: str, new_name: str) -> bool:
        """
        Renomeia um arquivo se ele existir.

        Args:
            old_name (str): Nome atual do arquivo.
            new_name (str): Novo nome para o arquivo.

        Returns:
            bool: True se o arquivo foi renomeado com sucesso, False se o arquivo não existir.
        """
        if os.path.exists(old_name):
            os.rename(old_name, new_name)
            logger.debug(f"Arquivo renomeado de '{old_name}' para '{new_name}'.")
            return True
        else:
            logger.warning(f"Aviso: O arquivo '{old_name}' não foi encontrado.")
            return False