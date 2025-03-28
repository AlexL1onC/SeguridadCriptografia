import os
from cryptography.fernet import Fernet
import shutil

def generate_key():
    """
    Genera una clave simétrica para cifrado.
    """
    return Fernet.generate_key()

def load_key(key_path='secret.key'):
    """
    Carga la clave de cifrado desde un archivo.
    Si el archivo no existe, genera una nueva clave y la guarda.
    """
    if os.path.exists(key_path):
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
    else:
        key = generate_key()
        with open(key_path, 'wb') as key_file:
            key_file.write(key)
    return key

def encrypt_file(input_file, output_file, key):
    """
    Encripta el contenido de input_file y lo guarda en output_file.
    """
    fernet = Fernet(key)
    with open(input_file, 'rb') as file:
        file_data = file.read()
    encrypted_data = fernet.encrypt(file_data)
    with open(output_file, 'wb') as file:
        file.write(encrypted_data)

def process_document(file_path, status, base_folder="documentos"):
    """
    Procesa un documento PDF realizando las siguientes acciones:
    
    1. Crea la estructura de directorios si no existen:
       - documentos/todos
       - documentos/sin_firmar
       - documentos/firmados
    2. Encripta el archivo original y lo guarda en la carpeta "todos".
    3. Dependiendo del estado ('sin_firmar' o 'firmado'),
       copia el archivo encriptado a la carpeta correspondiente.
    
    Parámetros:
    - file_path: Ruta del archivo PDF original.
    - status: Estado del documento. Debe ser "sin_firmar" o "firmado".
    - base_folder: Carpeta base donde se crearán las subcarpetas.
    """
    # Definición de las carpetas
    all_dir = os.path.join(base_folder, "todos")
    unsigned_dir = os.path.join(base_folder, "sin_firmar")
    signed_dir = os.path.join(base_folder, "firmados")
    os.makedirs(all_dir, exist_ok=True)
    os.makedirs(unsigned_dir, exist_ok=True)
    os.makedirs(signed_dir, exist_ok=True)

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
    print(f"Documento procesado y almacenado en:\n- Todos: {encrypted_file_path}\n- {status.replace('_', ' ').capitalize()}: {dest_path}")

if __name__ == '__main__':
    # Ejemplo de uso:
    # Supongamos que tenemos un archivo PDF llamado 'ejemplo.pdf' en el directorio actual.
    archivo = "ejemplo.pdf"
    # Definir el estado del documento: "sin_firmar" o "firmado"
    estado = "sin_firmar"  # o "firmado"
    
    # Procesa el documento
    process_document(archivo, estado)
