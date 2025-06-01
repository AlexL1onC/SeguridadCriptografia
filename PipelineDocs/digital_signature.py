from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
import os
import hashlib


# Parámetros
KEY_VAULT_URL = "https://legalbridge.vault.azure.net/"
KEY_NAME = "PythonEncryptationEC"

# Autenticación
credential = DefaultAzureCredential()
key_client = KeyClient(vault_url=KEY_VAULT_URL, credential=credential)
crypto_client = CryptographyClient(key_client.get_key(KEY_NAME), credential=credential)

def test_keyvault_connection():
    try:
        credential = DefaultAzureCredential()
        key_client = KeyClient(vault_url=KEY_VAULT_URL, credential=credential)
        key = key_client.get_key(KEY_NAME)
        print("Conexión a Key Vault exitosa. Clave encontrada:", key.name)
        return True
    except Exception as e:
        print("Fallo en Key Vault:", str(e))
        return False


def test_entra_id_connection():
    try:
        app = ConfidentialClientApplication(
            client_id=os.getenv("AZURE_CLIENT_ID"),
            authority=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}",
            client_credential=os.getenv("AZURE_CLIENT_SECRET")
        )
        result = app.acquire_token_silent(scopes=["User.Read"], account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=["User.Read"])
        print("Token obtenido de Entra ID (Expira en:", result['expires_in'], "segundos)")
        return True
    except Exception as e:
        print("Fallo en Entra ID:", str(e))
        return False

def firmar_archivo_bin(ruta_archivo, ruta_firma=None):
    with open(ruta_archivo, "rb") as f:
        contenido = f.read()
    digest = hashlib.sha256(contenido).digest()
    resultado = crypto_client.sign(SignatureAlgorithm.es256, digest)
    
    if ruta_firma:
        with open(ruta_firma, "wb") as f:
            f.write(resultado.signature)

    print(f"Documento firmado con Key Vault: {ruta_archivo}")
    return resultado.signature  # Esto es lo que guardas en la base de datos

def verificar_firma(ruta_archivo, ruta_firma):
    with open(ruta_archivo, "rb") as f:
        contenido = f.read()
    with open(ruta_firma, "rb") as f:
        firma = f.read()

    digest = hashlib.sha256(contenido).digest()  # Calcula el hash SHA-256

    resultado = crypto_client.verify(SignatureAlgorithm.es256, digest, firma)
    if resultado.is_valid:
        print("Firma válida (Key Vault)")
        return True
    else:
        print("Firma inválida (Key Vault)")
        return False

