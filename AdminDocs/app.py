from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import csv, os
from functools import wraps
from sqlalchemy import func

basedir = os.path.abspath(os.path.dirname(__file__))
parent_directory = os.path.join(basedir, os.pardir)
database_path = os.path.join(
    parent_directory, "PipelineDocs", "instance", "database.db"
)


app = Flask(__name__)
app.config["SECRET_KEY"] = "tu_clave_secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
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
    csv_path = os.path.join(os.path.dirname(__file__), "Ej_usuarios.csv")
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=",")  # Cambiar a coma <---
        # ... resto del código ...
        print("Campos CSV:", reader.fieldnames)  # para depurar
        for row in reader:
            usr = row.get("Usuario")
            pwd = row.get("Contraseña")
            rng = row.get("Rango")
            if not (usr and pwd and rng):
                continue  # omite líneas mal formateadas
            if not User.query.filter_by(username=usr).first():
                hashed = generate_password_hash(pwd)
                new_user = User(username=usr, password=hashed, rank=int(rng))
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
        print(user)
        if user and check_password_hash(user.password, password):
            if not user.admin:
                return "Usuario no es administrador", 401
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

    # Get documents by status counts
    status_data = db.session.query(Document.status, func.count(Document.id)).group_by(Document.status).all()
    # Format for Chart.js: { 'pending': 5, 'approved': 10, ... }
    documents_by_status = {status: count for status, count in status_data}

    # Get documents by category counts
    category_data = db.session.query(Document.category, func.count(Document.id)).group_by(Document.category).all()
    # Format for Chart.js: { 'Report': 3, 'Invoice': 7, ... }
    documents_by_category = {category: count for category, count in category_data}

    return render_template("dashboard.html",
                           user=user,
                           documents_by_status=documents_by_status,
                           documents_by_category=documents_by_category)




# -- Mis Documentos --
@app.route("/documentos", methods=["GET"])
@login_required
def mis_documentos():
    user = User.query.get(session["user_id"])
    estatus = request.args.get(
        "estatus", "todos"
    )
    query = Document.query.filter_by()

    if estatus == "enproceso":
        query = query.filter_by(status="pending")
    elif estatus == "aprobado":
        query = query.filter_by(status="approved")
    elif estatus == "rechazado":
        query = query.filter_by(status="rejected")

    documentos = query.all()  # Filtrar los documentos según el estatus
    return render_template("documentos.html", user=user, documentos=documentos)


# -- Logout --
@app.route("/logout", methods=["GET"])
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("login"))  # redirijo al login


if __name__ == "__main__":
    app.run(debug=True, port=5005)
