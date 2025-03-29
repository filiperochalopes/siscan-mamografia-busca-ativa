import sys
import os

# Garante que o diretório src esteja no caminho de importação
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.app import app  # importa o objeto Flask do src/app.py

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)