from pathlib import Path
from faker import Faker
from faker_file.providers.txt_file import TxtFileProvider
from faker_file.providers.pdf_file import PdfFileProvider
from faker_file.providers.pdf_file.generators.reportlab_generator import ReportlabPdfGenerator
from faker_file.storages.filesystem import FileSystemStorage

# Caminho onde os arquivos serão salvos
output_dir = Path(__file__).resolve().parents[2] / "tests" / "files"

# Cria o diretório se não existir
output_dir.mkdir(parents=True, exist_ok=True)

# Configura o armazenamento local
storage = FileSystemStorage(
    root_path=output_dir.parent,  # /tests
    rel_path="files"
)

# Instância do Faker
FAKER = Faker()
FAKER.add_provider(TxtFileProvider)
FAKER.add_provider(PdfFileProvider)

# Gera arquivo TXT com nome fixo: example.txt
txt_file = FAKER.txt_file(basename="example", extension="txt", storage=storage)
print(f"TXT gerado: {txt_file.data['filename']}")

# Gera arquivo PDF com nome fixo: invalid_pdf.pdf
pdf_file = FAKER.pdf_file(
    basename="invalid_pdf",
    extension="pdf",
    storage=storage,
    pdf_generator_cls=ReportlabPdfGenerator
)
print(f"PDF gerado: {pdf_file.data['filename']}")
