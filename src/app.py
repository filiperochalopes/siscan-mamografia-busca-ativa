from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from dotenv import load_dotenv
import os, time
from io import BytesIO

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
    
    processing_done = False
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            # Exibe overlay de carregamento (simulado via JS)
            # Aqui você pode implementar o processamento real do arquivo
            time.sleep(2)  # Simula tempo de processamento
            processing_done = True  # Sinaliza que o processamento foi concluído

    return render_template("upload.html.j2", processing_done=processing_done)

@app.route("/download")
def download():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    # Cria um arquivo CSV dummy para download (substitua pelo seu processamento)
    output = BytesIO()
    output.write(b"col1,col2,col3\n1,2,3\n4,5,6")
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, attachment_filename="planilha.csv")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)