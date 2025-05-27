from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import csv, os
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "tu_clave_secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

db = SQLAlchemy(app)


# --- Modelos ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))  # deja espacio para el hash
    rank = db.Column(db.Integer)
    admin = db.Column(db.Boolean)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(255))
    sender_id = db.Column(db.Integer)
    current_approver = db.Column(db.Integer)
    status = db.Column(db.String(20))  # pending, approved, rejected
    approvers = db.Column(db.String(255))  # IDs separados por comas
    category = db.Column(db.String(255))


# --- Carga de usuarios desde CSV (solo UTF-8 sin BOM) ---
def load_users():
    csv_path = os.path.join(os.path.dirname(__file__), "instance", "usuarios.csv")
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=",")  # Cambiar a coma <---
        # ... resto del código ...
        print("Campos CSV:", reader.fieldnames)  # para depurar
        for row in reader:
            usr = row.get("Usuario")
            pwd = row.get("Contraseña")
            rng = row.get("Rango")
            adm = row.get("Admin")
            adm_bol = adm.strip().lower() == "true"
            cat = row.get("Category")
            if not (usr and pwd and rng and adm):
                continue  # omite líneas mal formateadas
            if not User.query.filter_by(username=usr).first():
                hashed = generate_password_hash(pwd)
                new_user = User(
                    username=usr, password=hashed, rank=int(rng), admin=adm_bol
                )
                db.session.add(new_user)
        db.session.commit()


# --- Decorador de login ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


# --- Login ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        # comparamos hash con la contraseña recibida
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        return "Credenciales inválidas", 401
    return render_template("login.html")


# --- Dashboard ---
@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.get(session["user_id"])
    pending = Document.query.filter_by(current_approver=user.id).all()
    # docs = Document.query.all()
    return render_template("dashboard.html", user=user, documentos=pending)


# --- Enviar Documento --
@app.route("/enviar_documento", methods=["GET", "POST"])
@login_required
def enviar_documento():
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        file = request.files["documento"]
        category = request.form.get("category")
        approvers = request.form.getlist("approvers")

        if file and category and approvers:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            new_doc = Document(
                filename=filename,
                filepath=filepath,
                sender_id=session["user_id"],
                current_approver=approvers[0],
                status="pending",
                approvers=",".join(approvers),
                category=category,
            )
            db.session.add(new_doc)
            db.session.commit()
            return redirect(url_for("mis_documentos"))

    # Obtener usuarios disponibles según rango
    current_user = User.query.get(session["user_id"])
    users = User.query.filter(User.rank > current_user.rank).all()
    return render_template("enviar_documento.html", user=user, users=users)


# -- Aprobar Documento --
@app.route("/aprobar_documento/<int:doc_id>")
@login_required
def aprobar_documento(doc_id):
    doc = Document.query.get(doc_id)
    approvers = doc.approvers.split(",")
    current_index = approvers.index(str(doc.current_approver))

    if current_index < len(approvers) - 1:
        doc.current_approver = approvers[current_index + 1]
    else:
        doc.status = "approved"

    db.session.commit()
    return redirect(url_for("dashboard"))


# -- Mis Documentos --
@app.route("/mis_documentos", methods=["GET"])
@login_required
def mis_documentos():
    user = User.query.get(session["user_id"])
    estatus = request.args.get(
        "estatus", "todos"
    )  # Obtener el estatus de los parámetros de consulta
    query = Document.query.filter_by(
        sender_id=session["user_id"]
    )  # Filtrar por usuario actual

    if estatus == "enproceso":
        query = query.filter_by(status="pending")
    elif estatus == "aprobado":
        query = query.filter_by(status="approved")
    elif estatus == "rechazado":
        query = query.filter_by(status="rejected")

    documentos = query.all()  # Filtrar los documentos según el estatus
    return render_template("mis_documentos.html", user=user, documentos=documentos)


# -- Logout --
@app.route("/logout", methods=["GET"])
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("login"))  # redirijo al login


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_users()

    app.run(debug=True)
