from flask import (
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash,
    current_app,
    send_file,
)
from werkzeug.utils import secure_filename
import os
from . import bp
from utils.auth import user_required
from models import db, User, Document
from digital_signature import firmar_archivo_bin


@bp.before_request
def check_user():
    if not session.get("user_id") or session.get("is_admin"):
        return redirect(url_for("auth.login"))


@bp.route("/dashboard")
@user_required
def dashboard():
    user = User.query.get(session["user_id"])
    # Documentos donde el usuario es aprobador o remitente
    docs = Document.query.filter(
        (Document.sender_id == user.id) | (Document.approvers.contains(str(user.id)))
    ).order_by(Document.id.desc()).all()

    total = len(docs)
    firmados = sum(1 for d in docs if d.status == "approved")
    pendientes = sum(1 for d in docs if d.status == "pending")
    rechazados = sum(1 for d in docs if d.status == "rejected")
    # Ejemplo de espacio usado (puedes calcularlo si quieres)
    espacio_usado = sum(os.path.getsize(d.filepath) for d in docs if os.path.exists(d.filepath))
    espacio_usado_mb = round(espacio_usado / (1024 * 1024), 1)

    # Documentos recientes (últimos 4)
    recientes = docs[:4]

    return render_template(
        "user_dashboard.html",
        user=user,
        total=total,
        firmados=firmados,
        pendientes=pendientes,
        rechazados=rechazados,
        espacio_usado_mb=espacio_usado_mb,
        recientes=recientes,
    )


@bp.route("/enviar_documento", methods=["GET", "POST"])
@user_required
def enviar_documento():
    selected_approvers = request.form.getlist("approvers")
    user = User.query.get(session["user_id"])
    area = request.args.get("area", "")
    nivel = request.args.get("nivel", "")


    # Obtén todos los valores únicos de área y nivel para los selectores
    areas = [a[0] for a in db.session.query(User.area).distinct().all() if a[0]]
    niveles = sorted(set(u.rank for u in User.query.all()))

    # Filtra los usuarios aprobadores
    users_query = User.query.filter(User.rank > user.rank)
    if area:
        users_query = users_query.filter_by(area=area)
    if nivel:
        users_query = users_query.filter_by(rank=int(nivel))
    if selected_approvers:
        users_query = users_query.filter(~User.id.in_([int(a) for a in selected_approvers]))
    users = users_query.all()

    if request.method == "POST":
        file = request.files["documento"]
        category = request.form.get("category")
        approvers = request.form.getlist("approvers")

        if file and category and approvers:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Get the usernames of approvers for the message
            approver_users = User.query.filter(
                User.id.in_([int(id) for id in approvers])
            ).all()
            approver_names = [user.username for user in approver_users]

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

            flash(
                f'¡El documento "{filename}" ha sido enviado exitosamente! - Categoría: {category} - Aprobadores: {", ".join(approver_names)}',
                "success",
            )
            return redirect(url_for("user.mis_documentos"))
        else:
            if not file:
                flash("Por favor selecciona un archivo", "danger")
            if not category:
                flash("Por favor selecciona una categoría", "danger")
            if not approvers:
                flash("Por favor selecciona al menos un aprobador", "danger")

    selected_users = []
    if selected_approvers:
        selected_users = User.query.filter(User.id.in_([int(a) for a in selected_approvers])).all()

    return render_template(
        "user_enviar_documento.html",
        user=user,
        users=users,
        areas=areas,
        niveles=niveles,
        selected_users=selected_users,
        selected_approvers=selected_approvers,
    )


@bp.route("/previsualizar_documento/<int:doc_id>")
@user_required
def previsualizar_documento(doc_id):
    doc = Document.query.get(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    user = User.query.get(session["user_id"])
    # Solo puede acceder si es aprobador asignado y NO es el remitente
    if str(user.id) not in doc.approvers.split(",") or doc.sender_id == user.id:
        flash("No tienes permiso para firmar o rechazar este documento.", "danger")
        return redirect(url_for("user.dashboard"))
    return render_template("user_previsualizar_documento.html", doc=doc, user=user)


@bp.route("/aprobar_documento/<int:doc_id>", methods=["POST"])
@user_required
def aprobar_documento(doc_id):
    doc = Document.query.get(doc_id)
    approvers = doc.approvers.split(",")
    current_index = approvers.index(str(doc.current_approver))

    if current_index < len(approvers) - 1:
        doc.current_approver = approvers[current_index + 1]
        flash(
            f'Has aprobado el documento "{doc.filename}". El documento ha sido enviado al siguiente aprobador.',
            "success",
        )
    else:
        doc.status = "approved"
        doc.current_approver = None
        signature_bin = firmar_archivo_bin(doc.filepath)
        doc.signature_bin = signature_bin
        flash(
            f'¡El documento "{doc.filename}" ha sido firmado y aprobado exitosamente!',
            "success",
        )

    db.session.commit()
    return redirect(url_for("user.dashboard"))


@bp.route("/mis_documentos")
@user_required
def mis_documentos():
    user = User.query.get(session["user_id"])
    documentos_para_firmar = Document.query.filter(
        Document.current_approver == user.id,
        Document.status == "pending"
    ).all()
    documentos_esperando_firma = Document.query.filter(
        Document.sender_id == user.id,
        Document.status == "pending"
    ).all()
    documentos_almacenados = Document.query.filter(
        (Document.status == "approved") &
        (
            (Document.sender_id == user.id) |
            (Document.approvers.contains(str(user.id)))
        )
    ).all()
    # Obtener todos los usuarios relevantes
    user_ids = set()
    for doc in documentos_almacenados:
        user_ids.update([int(uid) for uid in doc.approvers.split(",") if uid.isdigit()])
    users = User.query.filter(User.id.in_(user_ids)).all()
    users_dict = {u.id: u.username for u in users}
    return render_template(
        "user_mis_documentos.html",
        user=user,
        documentos_para_firmar=documentos_para_firmar,
        documentos_esperando_firma=documentos_esperando_firma,
        documentos_almacenados=documentos_almacenados,
        users_dict=users_dict,
    )


@bp.route("/serve_documento/<int:doc_id>")
@user_required
def serve_documento(doc_id):
    doc = Document.query.get_or_404(doc_id)
    user = User.query.get(session["user_id"])

    # Check if user has permission to view this document
    if doc.sender_id != user.id and str(user.id) not in doc.approvers.split(","):
        return render_template("user_serve_documento_error.html", error_message="No tienes permiso para ver este documento")

    # Serve the file
    try:
        return send_file(doc.filepath, as_attachment=False)
    except Exception as e:
        return render_template("user_serve_documento_error.html", error_message=f"Error al cargar el documento: {str(e)}")


@bp.route("/ver_documento/<int:doc_id>")
@user_required
def ver_documento(doc_id):
    doc = Document.query.get(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    user = User.query.get(session["user_id"])
    return render_template("user_ver_documento.html", doc=doc, user=user)


@bp.route("/rechazar_documento/<int:doc_id>", methods=["POST"])
@user_required
def rechazar_documento(doc_id):
    doc = Document.query.get_or_404(doc_id)
    doc.status = "rejected"
    db.session.commit()
    flash("Documento rechazado correctamente.", "warning")
    return redirect(url_for("user.dashboard"))
