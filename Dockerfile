# Imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o requirements.txt e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia toda a aplicação (incluindo a pasta src/)
COPY . .

# Adiciona src ao PYTHONPATH
ENV PYTHONPATH=/app

# Expõe a porta 5000
EXPOSE 5000

# Inicia a aplicação
CMD ["python", "run.py"]