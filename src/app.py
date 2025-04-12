from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

from src.utils.validators import is_pdf
from src.services.config import Config

from src.services.mammography import ReportService

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        token = request.form.get("token")
        if token == app.config["TOKEN"]:
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
    error_message = None  # <-- novo para capturar erros

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename != "":
            # Verifica tipo de arquivo (simples: termina com .pdf)
            if not is_pdf(file):
                error_message = "Formato de arquivo inválido! Por favor envie um arquivo PDF."
                print(f"[DEBUG] Arquivo inválido recebido: {file.filename}", flush=True)
                return render_template("upload.html.j2", download_url=download_url or "", error_message=error_message)
            
            try:
                report_service = ReportService(file)
                download_url = report_service.build_excel()
            except ValueError as e:
                error_message = str(e)
                print(f"[DEBUG] Erro ao processar PDF: {error_message}", flush=True)
                return render_template("upload.html.j2", download_url=download_url or "", error_message=error_message)
            
    return render_template("upload.html.j2", download_url=download_url or "")