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

    download_url = None

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename != "":
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            nome_arquivo = f"resultado_processamento_laudos_siscan_{timestamp}.xlsx"
            export_dir = Path("src/static/exports")
            export_dir.mkdir(parents=True, exist_ok=True)

            # Salva arquivo e processa
            temp_pdf = Path("tmp/input.pdf")
            Path("tmp").mkdir(exist_ok=True)
            file.save(temp_pdf)

            extrator = SiscanReportMammographyExtract("tmp", "tmp")
            _, df = extrator.process()
            caminho_excel = export_dir / nome_arquivo
            extrator.save_to_excel(caminho_excel, sorted(extrator.df.columns))

            download_url = url_for('static', filename=f'exports/{nome_arquivo}')

    return render_template("upload.html.j2", download_url=download_url or "")

@app.route("/download")
def download():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    # Cria um arquivo CSV dummy para download (substitua pelo seu processamento)
    output = BytesIO()
    output.write(b"col1,col2,col3\n1,2,3\n4,5,6")
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, attachment_filename="planilha.csv")