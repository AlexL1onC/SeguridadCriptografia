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
    pending = Document.query.filter_by(current_approver=user.id).all()
    return render_template("user_dashboard.html", user=user, documentos=pending)


@bp.route("/enviar_documento", methods=["GET", "POST"])
@user_required
def enviar_documento():
    user = User.query.get(session["user_id"])
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

    current_user = User.query.get(session["user_id"])
    users = User.query.filter(User.rank > current_user.rank).all()
    return render_template("user_enviar_documento.html", user=user, users=users)


@bp.route("/previsualizar_documento/<int:doc_id>")
@user_required
def previsualizar_documento(doc_id):
    doc = Document.query.get(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    user = User.query.get(session["user_id"])
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
    estatus = request.args.get("estatus", "todos")
    query = Document.query.filter_by(sender_id=session["user_id"])

    if estatus == "enproceso":
        query = query.filter_by(status="pending")
    elif estatus == "aprobado":
        query = query.filter_by(status="approved")
    elif estatus == "rechazado":
        query = query.filter_by(status="rejected")

    documentos = query.all()
    return render_template("user_mis_documentos.html", user=user, documentos=documentos)


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
