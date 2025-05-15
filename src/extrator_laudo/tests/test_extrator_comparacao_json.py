import json
import os
import unittest
from pathlib import Path
from dotenv import load_dotenv
from src.extrator_laudo.mamografia import SiscanReportMammographyExtract

load_dotenv()

class TestExtratorComparacaoJSON(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent
        cls.laudos_dir = Path(os.getenv("TEST_FILES_DIR", cls.base_dir / "laudos"))
        cls.resultado_dir = cls.laudos_dir / "resultado"
        cls.pdf_teste = cls.laudos_dir / "example.pdf"
        cls.expected_json_path = cls.laudos_dir / "expected.json"

        assert cls.pdf_teste.exists(), f"Arquivo de teste não encontrado: {cls.pdf_teste}"
        assert cls.expected_json_path.exists(), f"Arquivo expected.json não encontrado: {cls.expected_json_path}"

        cls.resultado_dir.mkdir(exist_ok=True)

    def _normalizar_nulos(self, d: dict):
        return {
            k: (None if str(v).strip().lower() in ('nan', 'none', '') else v)
            for k, v in d.items()
        }

    def test_comparar_saida_com_json_esperado(self):
        extrator = SiscanReportMammographyExtract(self.laudos_dir, self.resultado_dir)

        _, df_resultado = extrator.process(selected_pages=[1, 84, 96, 129, 221])

        print(f"Comparando extração com expected.json: {self.expected_json_path}")
        print(f"Número de registros extraídos: {len(df_resultado)}")

        with open(self.expected_json_path, encoding="utf-8") as f:
            esperado_lista = json.load(f)

        self.assertEqual(
            len(df_resultado),
            len(esperado_lista),
            msg=f"Número de registros extraídos ({len(df_resultado)}) difere do esperado ({len(esperado_lista)})"
        )

        for idx, esperado in enumerate(esperado_lista):
            extraido = df_resultado.iloc[idx].to_dict()

            # Normaliza para string
            esperado_normalizado = {k.strip(): str(v).strip() for k, v in esperado.items()}
            extraido_normalizado = {k.strip(): str(v).strip() for k, v in extraido.items()}

            esperado_normalizado = self._normalizar_nulos(esperado_normalizado)
            extraido_normalizado = self._normalizar_nulos(extraido_normalizado)

            self.assertDictEqual(
                extraido_normalizado,
                esperado_normalizado,
                msg=f"Dados divergentes na linha {idx + 1}"
            )
