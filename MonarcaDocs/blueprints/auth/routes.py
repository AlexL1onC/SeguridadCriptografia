from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from . import bp
from models import User, db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session
    session.clear()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.admin
            
            # Redirect based on user type
            if user.admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
                
        flash('Credenciales inválidas', 'danger')
    return render_template('auth_login.html')

@bp.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('auth.login')) 