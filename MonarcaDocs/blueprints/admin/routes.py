from flask import render_template, session, redirect, url_for, request, flash, send_file
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from . import bp
from utils.auth import admin_required
from models import db, User, Document

@bp.before_request
def check_admin():
    if not session.get('user_id') or not session.get('is_admin'):
        return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@admin_required
def dashboard():
    user = User.query.get(session['user_id'])
    pending = Document.query.filter_by(current_approver=user.id).all()

    # Get documents by status counts
    status_data = db.session.query(
        Document.status, 
        func.count(Document.id)
    ).group_by(Document.status).all()
    # Format for Chart.js: { 'pending': 5, 'approved': 10, ... }
    documents_by_status = {status: count for status, count in status_data}

    # Get documents by category counts
    category_data = db.session.query(
        Document.category, 
        func.count(Document.id)
    ).group_by(Document.category).all()
    # Format for Chart.js: { 'Report': 3, 'Invoice': 7, ... }
    documents_by_category = {category: count for category, count in category_data}

    return render_template('admin_dashboard.html',
                         user=user,
                         documents_by_status=documents_by_status,
                         documents_by_category=documents_by_category)

@bp.route('/documentos')
@admin_required
def documentos():
    user = User.query.get(session['user_id'])
    estatus = request.args.get('estatus', 'todos')
    query = Document.query

    if estatus == 'enproceso':
        query = query.filter_by(status='pending')
    elif estatus == 'aprobado':
        query = query.filter_by(status='approved')
    elif estatus == 'rechazado':
        query = query.filter_by(status='rejected')

    documentos = query.all()
    return render_template('admin_documentos.html', user=user, documentos=documentos)

@bp.route('/usuarios')
@admin_required
def usuarios():
    user = User.query.get(session['user_id'])
    usuarios = User.query.all()
    return render_template('admin_usuarios.html', user=user, usuarios=usuarios)

@bp.route('/usuarios/agregar', methods=['POST'])
@admin_required
def agregar_usuario():
    username = request.form.get('username')
    password = request.form.get('password')
    rank = request.form.get('rank')
    is_admin = request.form.get('admin') == 'on'
    
    if not all([username, password, rank]):
        flash('Todos los campos son requeridos', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    if User.query.filter_by(username=username).first():
        flash('El nombre de usuario ya existe', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        rank=int(rank),
        admin=is_admin
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    flash('Usuario creado exitosamente', 'success')
    return redirect(url_for('admin.usuarios'))

@bp.route('/usuarios/editar/<int:user_id>', methods=['POST'])
@admin_required
def editar_usuario(user_id):
    if user_id == session.get('user_id'):
        flash('No puedes cambiar tu propio estado de administrador', 'danger')
        return redirect(url_for('admin.usuarios'))
        
    usuario = User.query.get_or_404(user_id)
    username = request.form.get('username')
    rank = request.form.get('rank')
    password = request.form.get('password')
    is_admin = request.form.get('admin') == 'on'
    
    if not all([username, rank]):
        flash('El nombre de usuario y rango son requeridos', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    # Check if username exists and it's not the same user
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user_id:
        flash('El nombre de usuario ya existe', 'danger')
        return redirect(url_for('admin.usuarios'))
    
    usuario.username = username
    usuario.rank = int(rank)
    usuario.admin = is_admin
    
    if password:  # Only update password if provided
        usuario.password = generate_password_hash(password)
    
    db.session.commit()
    flash('Usuario actualizado exitosamente', 'success')
    return redirect(url_for('admin.usuarios'))

@bp.route('/usuarios/eliminar/<int:user_id>', methods=['POST'])
@admin_required
def eliminar_usuario(user_id):
    if user_id == session.get('user_id'):
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.usuarios'))
        
    usuario = User.query.get_or_404(user_id)
    db.session.delete(usuario)
    db.session.commit()
    
    flash('Usuario eliminado exitosamente', 'success')
    return redirect(url_for('admin.usuarios'))

@bp.route('/ver_documento/<int:doc_id>')
@admin_required
def ver_documento(doc_id):
    doc = Document.query.get(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    user = User.query.get(session["user_id"])
    return render_template("admin_ver_documento.html", doc=doc, user=user)

@bp.route("/serve_documento/<int:doc_id>")
@admin_required
def serve_documento(doc_id):
    try:
        doc = Document.query.get_or_404(doc_id)
        return send_file(doc.filepath, as_attachment=False)
    except Exception as e:
        return render_template("admin_serve_documento_error.html", error_message=f"Error al cargar el documento: {str(e)}") 