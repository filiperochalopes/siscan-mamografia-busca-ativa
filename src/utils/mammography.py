from datetime import datetime
import numpy as np
import pandas as pd


def extrair_birads(texto):
    try:
        # Divide a string e pega o segundo elemento (número)
        numero = int(texto.split()[1])
        return numero
    except Exception:
        return np.nan


# Calcula a idade a partir da data de nascimento
def calcular_idade(data_nascimento):
    if pd.isna(data_nascimento):
        return np.nan
    hoje = datetime.today().date()
    try:
        # Se a data vem como string, converte para datetime (assumindo formato dia/mês/ano)
        if isinstance(data_nascimento, str):
            data_nascimento = pd.to_datetime(data_nascimento, dayfirst=True).date()
        else:
            data_nascimento = data_nascimento.date()
        idade = (
            hoje.year
            - data_nascimento.year
            - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
        )
        return idade
    except Exception:
        return np.nan


# Verifica se a mama é densa: retorna 1 se o valor for "Predominantemente Densa" ou "Densa"
def is_densa(tipo_de_mama):
    return 1 if tipo_de_mama in ["Predominantemente Densa", "Densa"] else 0


# Verifica se há indicação para USG, usando vários campos
def verificar_usg(row):
    # Se alguma mama for densa
    if is_densa(row.get("resultado_exame__mama_direita__tipo_de_mama", "")) or is_densa(
        row.get("resultado_exame__mama_esquerda__tipo_de_mama", "")
    ):
        return 1
    # Se na classificação radiológica aparecer "Categoria 0"
    if "Categoria 0" in str(
        row.get("resultado_exame__classificacao_radiologica__mama_direita", "")
    ) or "Categoria 0" in str(
        row.get("resultado_exame__classificacao_radiologica__mama_esquerda", "")
    ):
        return 1
    # Se em recomendações constar "Complemento com ultrassonografia"
    if "Complemento com ultrassonografia" in str(
        row.get("resultado_exame__recomendacoes", "")
    ):
        return 1
    return 0


# Define a coluna "Alterado" com base no BIRADS e se há indicação para USG
def definir_alterado(row, birads_md, birads_me, usg):
    # Se qualquer lado apresentar BIRADS 4 ou superior, marca 2
    if (not np.isnan(birads_md) and birads_md >= 4) or (
        not np.isnan(birads_me) and birads_me >= 4
    ):
        return 2
    # Se qualquer lado tiver BIRADS 3 ou se houver indicação de USG, marca 1
    if (birads_md == 3 or birads_me == 3) or usg == 1:
        return 1
    # Caso contrário, marca 0 (BIRADS 1 ou 2)
    return 0
