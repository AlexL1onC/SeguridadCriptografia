import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
BASE_FOLDER = 'documentos'

# Asegurarse de que existan las carpetas necesarias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE_FOLDER, "todos"), exist_ok=True)
os.makedirs(os.path.join(BASE_FOLDER, "sin_firmar"), exist_ok=True)
os.makedirs(os.path.join(BASE_FOLDER, "firmados"), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_key():
    return Fernet.generate_key()

def load_key(key_path='secret.key'):
    if os.path.exists(key_path):
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
    else:
        key = generate_key()
        with open(key_path, 'wb') as key_file:
            key_file.write(key)
    return key

def encrypt_file(input_file, output_file, key):
    fernet = Fernet(key)
    with open(input_file, 'rb') as file:
        file_data = file.read()
    encrypted_data = fernet.encrypt(file_data)
    with open(output_file, 'wb') as file:
        file.write(encrypted_data)

def process_document(file_path, status, base_folder=BASE_FOLDER):
    # Definición de las carpetas destino
    all_dir = os.path.join(base_folder, "todos")
    unsigned_dir = os.path.join(base_folder, "sin_firmar")
    signed_dir = os.path.join(base_folder, "firmados")

    # Cargar o generar la clave de cifrado
    key = load_key()

    # Encriptar el archivo y guardarlo en la carpeta "todos"
    file_name = os.path.basename(file_path)
    encrypted_file_path = os.path.join(all_dir, file_name)
    encrypt_file(file_path, encrypted_file_path, key)

    # Dependiendo del estado, copiar el archivo encriptado a la carpeta correspondiente
    if status == "sin_firmar":
        dest_path = os.path.join(unsigned_dir, file_name)
    elif status == "firmado":
        dest_path = os.path.join(signed_dir, file_name)
    else:
        raise ValueError("Estado no reconocido. Use 'sin_firmar' o 'firmado'.")
    
    shutil.copy(encrypted_file_path, dest_path)
    return {
        "todos": encrypted_file_path,
        "estado": dest_path,
        "status": status
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró el archivo"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Se espera recibir el estatus como parte del formulario
        status = request.form.get("status", "sin_firmar")
        try:
            result = process_document(file_path, status)
            return jsonify({"message": "Documento procesado", "data": result})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Archivo no permitido"}), 400

@app.route('/documents', methods=['GET'])
def list_documents():
    """
    Devuelve la lista de documentos almacenados en las carpetas.
    """
    documentos = {
        "todos": os.listdir(os.path.join(BASE_FOLDER, "todos")),
        "sin_firmar": os.listdir(os.path.join(BASE_FOLDER, "sin_firmar")),
        "firmados": os.listdir(os.path.join(BASE_FOLDER, "firmados"))
    }
    return jsonify(documentos)

@app.route('/document/<folder>/<filename>')
def serve_document(folder, filename):
    """
    Sirve un documento encriptado. Puedes crear otro endpoint para desencriptarlo si es necesario.
    """
    if folder not in ["todos", "sin_firmar", "firmados"]:
        return jsonify({"error": "Carpeta no válida"}), 400
    directory = os.path.join(BASE_FOLDER, folder)
    return send_from_directory(directory, filename)

if __name__ == '__main__':
    app.run(debug=True)
