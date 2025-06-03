import os
from flask import Flask, redirect, url_for
from models import db
from blueprints.auth import bp as auth_bp
from blueprints.user import bp as user_bp
from blueprints.admin import bp as admin_bp
from app_init import init_directories, init_database
from utils.filters import nl2br


def create_app():

    # Crea aplicación Flask
    app = Flask(__name__)

    # Initialize directories and get paths
    base_dir, instance_dir, uploads_dir = init_directories(app)
    database_path = os.path.join(base_dir, "instance", "database.db")

    # Configuration
    app.config["SECRET_KEY"] = "tu_clave_secreta"  # Change this to a secure secret key
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = uploads_dir

    # Initialize extensions
    db.init_app(app)

    # Register custom filters
    app.jinja_env.filters['nl2br'] = nl2br

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Root URL redirect to login
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # Initialize database and load initial data
    init_database(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
