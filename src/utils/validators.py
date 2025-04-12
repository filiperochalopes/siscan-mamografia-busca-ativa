def is_pdf(file):
    """
    Verifica se o arquivo é um PDF válido, verificando o tipo MIME e a extensão.
    """
    return file.mimetype == "application/pdf" and file.filename.lower().endswith(".pdf")

def is_valid_siscan_df(df):
    """
    Verifica se o DataFrame é válido como laudo SISCAN.
    """
    return not df.empty and df["paciente__nome"].any()