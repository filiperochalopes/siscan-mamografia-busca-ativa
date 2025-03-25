class CorruptedDocumentError(Exception):
    def __init__(self, message="Falha ao abrir o documento."):
        self.message = message
        super().__init__(self.message)


class EmptyDocumentError(Exception):
    def __init__(self, message="O documento PDF está vazio."):
        self.message = message
        super().__init__(self.message)