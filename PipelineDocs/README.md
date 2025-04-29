# Monarca Docs

Monarca Docs es una aplicación web diseñada para gestionar documentos de manera segura, permitiendo su envío, aprobación y seguimiento. Está construida con Flask y utiliza una base de datos SQLite para almacenar usuarios y documentos.

## Funcionalidades Principales

1. **Inicio de Sesión**:
   - Los usuarios pueden iniciar sesión con credenciales almacenadas en la base de datos.
   - Las contraseñas están protegidas mediante hashing.

2. **Dashboard**:
   - Muestra los documentos pendientes de aprobación para el usuario actual.
   - Permite aprobar documentos si el usuario tiene los permisos necesarios.

3. **Enviar Documento**:
   - Los usuarios pueden cargar documentos y seleccionar destinatarios para su aprobación.
   - Los documentos se almacenan en un directorio local y se registran en la base de datos.

4. **Mis Documentos**:
   - Los usuarios pueden ver los documentos que han enviado, filtrados por estatus (Todos, En Proceso, Aprobado, Rechazado).

5. **Aprobar Documento**:
   - Los usuarios con permisos pueden aprobar documentos. Si hay múltiples aprobadores, el documento pasa al siguiente aprobador.

6. **Cerrar Sesión**:
   - Los usuarios pueden cerrar sesión para proteger su cuenta.

## Estructura de la Base de Datos

- **User**:
  - `id`: Identificador único.
  - `username`: Nombre de usuario.
  - `password`: Contraseña (almacenada como hash).
  - `rank`: Nivel de rango del usuario.

- **Document**:
  - `id`: Identificador único.
  - `filename`: Nombre del archivo.
  - `filepath`: Ruta del archivo en el servidor.
  - `sender_id`: ID del usuario que envió el documento.
  - `current_approver`: ID del aprobador actual.
  - `status`: Estado del documento (`pending`, `approved`, `rejected`).
  - `approvers`: Lista de IDs de aprobadores separados por comas.

## Plantillas HTML

- **`login.html`**:
  - Formulario para iniciar sesión.

- **`dashboard.html`**:
  - Muestra los documentos pendientes de aprobación.

- **`enviar_documento.html`**:
  - Permite cargar un documento y seleccionar aprobadores.

- **`mis_documentos.html`**:
  - Lista los documentos enviados por el usuario, con opciones de filtro por estatus.

## Archivos Clave

- **`app.py`**:
  - Contiene la lógica principal de la aplicación, incluyendo rutas, modelos y funciones auxiliares.

- **`style.css`**:
  - Archivo de estilos para personalizar la apariencia de la aplicación.

- **`Ej_usuarios.csv`**:
  - Archivo CSV utilizado para cargar usuarios iniciales en la base de datos.

## Cómo Ejecutar

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

3. Acceder a la aplicación en el navegador:
   ```
   http://127.0.0.1:5000
   ```

## Notas

- Los documentos se almacenan en el directorio `uploads`.
- Asegúrate de que el archivo `Ej_usuarios.csv` esté en el mismo directorio que `app.py` y tenga formato UTF-8 sin BOM.
