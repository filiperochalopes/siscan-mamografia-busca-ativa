import logging
from typing import Any, Dict, List, Optional

from src.extrator_laudo.base import SiscanReportExtractor

logger = logging.getLogger(__name__)


class SiscanReportMammographyExtract(SiscanReportExtractor):
    def get_ignore_lines(self) -> List[str]:
        return ["SISCAN - Sistema de informação do Câncer", "LAUDO DO EXAME DE MAMOGRAFIA"]

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
        return {
            None: ["Emissão:", "Hora:", "Página:", "UF",
                   "Data da solicitação:",
                   "Nº do exame:", "Nº do protocolo:", "Nº do prontuário:"],
            "RESPONSÁVEL PELO RESULTADO": ["Data da liberação do resultado:"],
            "PACIENTE": ["Telefone"]
        }

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
        return {
            "UNIDADE DE SAÚDE": {
                "fields": ["Nome:", "CNES:", "UF:", "Município:"],
                "subsections": [],
                "subsections_coordinate_x0": None,
            },
            "PACIENTE": {
                "fields": [],
                "subsections": [],
                "subsections_coordinate_x0": None,
            },
            "PRESTADOR DE SERVIÇO": {
                "fields": [],
                "subsections": [],
                "subsections_coordinate_x0": None,
            },
            "RESULTADO EXAME": {
                "fields": [],
                "subsections": [],
                "subsections_coordinate_x0": 36.00,
            },
            "RESPONSÁVEL PELO RESULTADO": {
                "fields": [],
                "subsections": [],
                "subsections_coordinate_x0": None,
            },
        }