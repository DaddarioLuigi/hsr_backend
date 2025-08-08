# utils/drive_uploader.py
import io
import mimetypes
import os
import json
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scope per upload e gestione file; configurabile via env per evitare verifiche stringenti in OAuth
_SCOPES_DEFAULT = 'https://www.googleapis.com/auth/drive'
SCOPES = [s.strip() for s in (os.getenv('GOOGLE_DRIVE_SCOPES', _SCOPES_DEFAULT)).split(',') if s.strip()]


def _get_user_oauth_credentials() -> Credentials:
    """Ottiene credenziali OAuth utente (My Drive) usando client secrets e token.
    Env supportati:
      - GOOGLE_OAUTH_CLIENT_SECRETS_JSON: JSON del client OAuth
      - GOOGLE_OAUTH_CLIENT_SECRETS: path al client_secret.json (fallback)
      - GOOGLE_OAUTH_TOKEN_JSON: JSON del token OAuth
      - GOOGLE_OAUTH_TOKEN_PATH: path al token.json (fallback)
    """
    secrets_json = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS_JSON")
    secrets_path = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "client_secret.json")
    token_json = os.getenv("GOOGLE_OAUTH_TOKEN_JSON")
    token_path = os.getenv("GOOGLE_OAUTH_TOKEN_PATH", "token.json")

    creds: Credentials | None = None
    # 1) token via env json
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except Exception:
            creds = None
    # 2) token via file
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Avvia flow OAuth con client secrets da JSON env o file
            if secrets_json:
                flow = InstalledAppFlow.from_client_config(json.loads(secrets_json), SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Salva token su file se possibile (opzionale in deploy)
        try:
            with open(token_path, "w", encoding="utf-8") as token_f:
                token_f.write(creds.to_json())
        except Exception:
            pass
    return creds

@lru_cache(maxsize=1)
def get_drive_service():
    """
    Costruisce il client Drive usando:
    - Modalità utente OAuth (se DRIVE_AUTH_MODE=user)
    - Altrimenti Service Account
    - Fallback: token OAuth locale/env
    """
    auth_mode = (os.getenv("DRIVE_AUTH_MODE") or "").lower()

    if auth_mode == "user":
        creds = _get_user_oauth_credentials()
        return build('drive', 'v3', credentials=creds)

    json_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    file_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if json_env:
        try:
            info = json.loads(json_env)
            creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            return build('drive', 'v3', credentials=creds)
        except Exception as exc:
            raise RuntimeError("Credenziali in GOOGLE_SERVICE_ACCOUNT_JSON non valide") from exc
    if file_path:
        try:
            creds = service_account.Credentials.from_service_account_file(file_path, scopes=SCOPES)
            return build('drive', 'v3', credentials=creds)
        except Exception as exc:
            raise RuntimeError("Impossibile leggere il file indicato in GOOGLE_APPLICATION_CREDENTIALS") from exc

    # Fallback: se esiste token OAuth locale, usalo
    token_path = os.getenv("GOOGLE_OAUTH_TOKEN_PATH", "token.json")
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())
        return build('drive', 'v3', credentials=creds)

    raise RuntimeError(
        "Nessuna credenziale Drive trovata. Imposta DRIVE_AUTH_MODE=user con OAuth, oppure configura il Service Account."
    )


def upload_to_drive(local_path: str, drive_folder_id: str) -> dict:
    """Carica il file su Google Drive nella cartella specificata.

    Ritorna il dict con 'id' e 'webViewLink'. Il tipo MIME viene
    determinato automaticamente in base all'estensione del file.
    """
    service = get_drive_service()

    file_metadata = {
        "name": os.path.basename(local_path),
        "parents": [drive_folder_id],
    }
    mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    media = MediaFileUpload(local_path, mimetype=mime_type)
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink", supportsAllDrives=True)
        .execute()
    )
    return file


def ensure_folder(name: str, parent_id: str) -> str:
    """Restituisce l'ID di una cartella esistente o la crea."""
    service = get_drive_service()

    query = (
        f"'{parent_id}' in parents and name='{name}' and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    result = (
        service.files()
        .list(q=query, fields="files(id)", spaces="drive", includeItemsFromAllDrives=True, supportsAllDrives=True)
        .execute()
    )
    files = result.get("files", [])
    if files:
        return files[0]["id"]

    folder_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = (
        service.files()
        .create(body=folder_metadata, fields="id", supportsAllDrives=True)
        .execute()
    )
    return folder["id"]


def ensure_path(parent_id: str, parts: list[str]) -> str:
    """Assicura una catena di cartelle (annidate) restituendo l'ID finale."""
    current = parent_id
    for part in parts:
        current = ensure_folder(part, current)
    return current


def upload_or_update_file(local_path: str, parent_id: str) -> dict:
    """Crea o aggiorna un file (stesso nome) nella cartella indicata, evitando duplicati."""
    service = get_drive_service()
    name = os.path.basename(local_path)

    # cerca file esistente con stesso nome
    query = f"'{parent_id}' in parents and name='{name}' and trashed=false"
    res = service.files().list(q=query, fields="files(id)", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = res.get("files", [])

    mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    media = MediaFileUpload(local_path, mimetype=mime_type, resumable=False)

    if files:
        file_id = files[0]["id"]
        updated = service.files().update(fileId=file_id, media_body=media, fields="id, webViewLink", supportsAllDrives=True).execute()
        return updated
    else:
        meta = {"name": name, "parents": [parent_id]}
        created = service.files().create(body=meta, media_body=media, fields="id, webViewLink", supportsAllDrives=True).execute()
        return created


def download_from_drive(file_id: str) -> bytes:
    """Scarica il contenuto di un file da Drive e lo restituisce come bytes."""
    service = get_drive_service()

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read()


def list_folders(parent_id: str) -> list[dict]:
    """Ritorna lista di cartelle (id, name) sotto parent_id."""
    service = get_drive_service()
    query = (
        f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    items: list[dict] = []
    page_token = None
    while True:
        res = service.files().list(q=query, fields="nextPageToken, files(id, name)", pageToken=page_token, spaces="drive", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
        items.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return items


def list_files(parent_id: str, mime_type: str | None = None, fields: str = "files(id,name,mimeType,webViewLink,modifiedTime)") -> list[dict]:
    """Ritorna lista di file sotto parent_id; opzionale filtro per mimeType."""
    service = get_drive_service()
    base = f"'{parent_id}' in parents and trashed=false"
    if mime_type:
        base += f" and mimeType='{mime_type}'"
    items: list[dict] = []
    page_token = None
    while True:
        res = service.files().list(q=base, fields=f"nextPageToken, {fields}", pageToken=page_token, spaces="drive", includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
        items.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    return items


def find_file_by_name(parent_id: str, name: str, fields: str = "files(id,name,mimeType,webViewLink,modifiedTime)") -> dict | None:
    """Cerca un file per nome esatto in una cartella."""
    service = get_drive_service()
    query = f"'{parent_id}' in parents and name='{name}' and trashed=false"
    res = service.files().list(q=query, fields=fields, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
    files = res.get("files", [])
    return files[0] if files else None
