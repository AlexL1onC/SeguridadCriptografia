# Monarca Docs

Monarca Docs es una aplicación web diseñada para gestionar documentos de manera segura, permitiendo su envío, aprobación y seguimiento. Está construida con Flask y utiliza una base de datos SQLite para almacenar usuarios y documentos, con integración de Azure Key Vault para firmas digitales.

## Funcionalidades Principales

1. **Inicio de Sesión Seguro**:
   - Los usuarios pueden iniciar sesión con credenciales almacenadas en la base de datos.
   - Las contraseñas están protegidas mediante hashing seguro con Werkzeug.
   - Sistema de sesiones para mantener la seguridad entre peticiones.

2. **Interfaz Principal**:
   - Vista personalizada según el tipo de usuario (normal o administrador).
   - Para usuarios normales: visualización de documentos pendientes de revisión.
   - Para administradores: panel con estadísticas y gráficos de documentos por estado y categoría.

3. **Gestión de Documentos**:
   - Carga de documentos con categorización.
   - Sistema de aprobación jerárquico basado en rangos de usuario.
   - Firma digital de documentos usando Azure Key Vault.
   - Almacenamiento seguro en el sistema de archivos local.

4. **Sistema de Aprobación Avanzado**:
   - Flujo de aprobación basado en jerarquía de usuarios.
   - Solo usuarios de rango superior pueden aprobar documentos.
   - Seguimiento del estado del documento (Pendiente, Aprobado, Rechazado).
   - Visualización de documentos directamente en el navegador.

5. **Panel de Administración**:
   - Gestión completa de usuarios (crear, ver, modificar).
   - Asignación de roles y rangos administrativos.
   - Monitoreo de documentos y estadísticas del sistema.

6. **Seguridad Integrada**:
   - Integración con Azure Key Vault para firmas digitales.
   - Autenticación con Azure Entra ID.
   - Protección contra accesos no autorizados mediante decoradores.
   - Validación de permisos en cada operación.

## Estructura de la Base de Datos

### User
- `id`: Identificador único
- `username`: Nombre de usuario (único)
- `password`: Contraseña (hash seguro)
- `admin`: Booleano para privilegios administrativos
- `rank`: Nivel jerárquico para aprobaciones

### Document
- `id`: Identificador único
- `filename`: Nombre del archivo
- `filepath`: Ruta del archivo en el servidor
- `sender_id`: ID del usuario que envió el documento
- `current_approver`: ID del aprobador actual
- `status`: Estado del documento (`pending`, `approved`, `rejected`)
- `approvers`: Lista de IDs de aprobadores (separados por comas)
- `category`: Categoría del documento

## Arquitectura del Proyecto

```
MonarcaDocs/
├── app.py                 # Aplicación principal Flask
├── app_init.py           # Inicialización de la aplicación
├── models.py             # Modelos de la base de datos
├── digital_signature.py  # Integración con Azure Key Vault
├── requirements.txt      # Dependencias del proyecto
├── blueprints/          # Módulos de la aplicación
│   ├── admin/          # Funcionalidades de administración
│   ├── auth/           # Autenticación y autorización
│   └── user/           # Funcionalidades de usuario
├── static/             # Archivos estáticos (CSS, JS)
├── templates/          # Plantillas HTML
├── uploads/           # Almacenamiento de documentos
└── utils/             # Utilidades y helpers
```

## Requisitos del Sistema

- Python 3.8 o superior
- Cuenta de Azure con Key Vault configurado
- Variables de entorno configuradas:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_CLIENT_SECRET`

## Dependencias Principales

```
flask
flask_sqlalchemy
werkzeug
azure-identity>=1.12.0
azure-keyvault-keys>=4.8.0
azure-keyvault-secrets>=4.7.0
msal>=1.22.0
python-dotenv>=1.0.0
SQLAlchemy
```

## Instalación y Configuración

1. Clonar el repositorio:
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd MonarcaDocs
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   - Crear archivo `.env` en la raíz del proyecto
   - Agregar credenciales de Azure y configuración necesaria

5. Inicializar la base de datos:
   ```bash
   python app.py
   ```

6. Acceder a la aplicación:
   ```
   http://127.0.0.1:5000
   ```

## Seguridad y Buenas Prácticas

1. **Almacenamiento de Documentos**:
   - Los documentos se almacenan en el directorio `uploads/`
   - Nombres de archivo sanitizados para prevenir ataques
   - Verificación de tipos de archivo permitidos

2. **Autenticación y Autorización**:
   - Sistema de roles basado en rangos
   - Decoradores para protección de rutas
   - Validación de sesiones activas

3. **Firmas Digitales**:
   - Integración con Azure Key Vault
   - Algoritmo ES256 para firmas
   - Verificación de integridad de documentos

## Notas de Desarrollo

- Asegurarse de que el archivo `.env` esté configurado correctamente
- Los archivos de usuarios iniciales deben estar en formato UTF-8 sin BOM
- Mantener actualizadas las dependencias de Azure para características de seguridad
- Revisar periódicamente los logs de acceso y operaciones
