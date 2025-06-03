from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    admin = db.Column(db.Boolean, default=False)
    rank = db.Column(db.Integer)  # Added for document approval workflow

    def __init__(self, username, password, admin=False, rank=0):
        self.username = username
        self.password = generate_password_hash(password)
        self.admin = admin
        self.rank = rank

    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(255))
    sender_id = db.Column(db.Integer)
    current_approver = db.Column(db.Integer)
    status = db.Column(db.String(20))  # pending, approved, rejected
    approvers = db.Column(db.String(255))  # IDs separated by comas
    category = db.Column(db.String(255))
    signature_bin = db.Column(db.LargeBinary) 