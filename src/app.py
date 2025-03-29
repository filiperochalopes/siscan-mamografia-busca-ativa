from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from dotenv import load_dotenv
import os, time
from io import BytesIO
from pathlib import Path
from datetime import datetime
from src.extrator_laudo.mamografia import SiscanReportMammographyExtract

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "minha_chave_secreta")  # Utilize uma chave segura em produção
TOKEN = os.getenv("TOKEN")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token")
        if token == TOKEN:
            session["logged_in"] = True
            return redirect(url_for("upload"))
        else:
            flash("Token incorreto!")
    return render_template("login.html.j2")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        print("Processando arquivo...", flush=True)
        file = request.files.get("file")
        print("Arquivo recebido:", file, flush=True)
        print("Nome do arquivo:", getattr(file, "filename", None), flush=True)
        print("Tamanho (stream):", file.stream.tell() if file else "sem stream", flush=True)
        if file:
            temp_dir = Path("tmp")
            temp_dir.mkdir(exist_ok=True)
            pdf_path = temp_dir / file.filename
            file.save(pdf_path)
            print("Arquivo salvo em:", pdf_path, flush=True)

            extrator = SiscanReportMammographyExtract(str(temp_dir), str(temp_dir))
            _, df = extrator.process()

            # Gera timestamp no formato yyyymmddhhmm
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            nome_arquivo = f"resultado_processamento_laudos_siscan_{timestamp}.xlsx"
            caminho_excel = f"/app/src/static/exports/{nome_arquivo}"

            extrator.save_to_excel(caminho_excel, sorted(extrator.df.columns))
            print("Arquivo Excel gerado com sucesso!", flush=True)

            return send_file(caminho_excel, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=nome_arquivo)

    return render_template("upload.html.j2")

@app.route("/download")
def download():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    # Cria um arquivo CSV dummy para download (substitua pelo seu processamento)
    output = BytesIO()
    output.write(b"col1,col2,col3\n1,2,3\n4,5,6")
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, attachment_filename="planilha.csv")