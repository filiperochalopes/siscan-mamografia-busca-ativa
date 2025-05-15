# Imagem base oficial do Python
FROM python:3.11-slim

# Instalar curl
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* \

# Define o diretório de trabalho
WORKDIR /app

# Copia o requirements.txt e instala as dependências
COPY requirements.txt .

# Instala dependências somente se o requirements.txt mudar
RUN pip install --no-cache-dir -r requirements.txt

# Instala o Playwright e os navegadores necessários
# RUN playwright install
RUN python -m playwright install --with-deps


# Copia toda a aplicação (incluindo a pasta src/)
COPY . .

# Adiciona src ao PYTHONPATH
ENV PYTHONPATH=/app/src

# Expõe a porta 5000
EXPOSE 5000

# Inicia a aplicação
CMD ["python", "run.py"]