import logging
from typing import Any, Dict, List

from src.extrator_laudo.base import SiscanReportExtractor

logger = logging.getLogger(__name__)


class SiscanReportMammographyExtract(SiscanReportExtractor):
    def get_ignore_lines(self) -> List[str]:
        return ["SISCAN - Sistema de informação do Câncer", "LAUDO DO EXAME DE MAMOGRAFIA"]

    def get_fields(self) -> Dict[str, Any]:
        return {
            None: ["Emissão:", "Hora:", "Página:", "UF"],
            "RESPONSÁVEL PELO RESULTADO": ["Data da liberação do resultado:"],
            "PACIENTE": ["Telefone"]
        }

    def get_sections_all(self) -> List[str]:
        return [
            "UNIDADE DE SAÚDE",
            "PACIENTE",
            "PRESTADOR DE SERVIÇO",
            "RESULTADO EXAME",
            "RESPONSÁVEL PELO RESULTADO"
        ]