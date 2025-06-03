import os
import csv
from models import db, User

def init_directories(app):
    """Create necessary directories if they don't exist."""
    # Get absolute paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(base_dir, "instance")
    uploads_dir = os.path.join(base_dir, "uploads")
    
    # Ensure instance directory exists
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    # Ensure upload directory exists
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    return base_dir, instance_dir, uploads_dir

def load_initial_users(app):
    """Load initial users from CSV file."""
    instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
    csv_path = os.path.join(instance_dir, "usuarios.csv")
    
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                usr = row.get("Usuario")
                pwd = row.get("Contraseña")
                rng = row.get("Rango")
                adm = row.get("Admin")

                if not (usr and pwd and rng and adm):
                    continue

                if not User.query.filter_by(username=usr).first():
                    new_user = User(
                        username=usr,
                        password=pwd,
                        rank=int(rng),
                        admin=adm.strip().lower() == "true",
                    )
                    db.session.add(new_user)
            db.session.commit()
    except FileNotFoundError:
        print("Warning: usuarios.csv not found in instance directory")
    except Exception as e:
        print(f"Error loading users: {e}")

def init_database(app):
    """Initialize database and load initial data."""
    with app.app_context():
        db.create_all()
        load_initial_users(app) 