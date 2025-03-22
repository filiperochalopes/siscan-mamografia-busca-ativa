# Imagem base oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o requirements.txt e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY /src .

# Expõe a porta 5000
EXPOSE 5000

# Inicia a aplicação
CMD ["python", "app.py"]