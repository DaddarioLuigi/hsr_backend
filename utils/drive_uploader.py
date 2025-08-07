# utils/drive_uploader.py
import io
import mimetypes
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Scope per upload “file.only”
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Inizializza le credenziali e il servizio Drive
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=creds)

def upload_to_drive(local_path: str, drive_folder_id: str) -> dict:
    """Carica il file su Google Drive nella cartella specificata.

    Ritorna il dict con 'id' e 'webViewLink'. Il tipo MIME viene
    determinato automaticamente in base all'estensione del file.
    """

    file_metadata = {
        "name": os.path.basename(local_path),
        "parents": [drive_folder_id],
    }
    mime_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    media = MediaFileUpload(local_path, mimetype=mime_type)
    file = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="id, webViewLink")
        .execute()
    )
    return file


def ensure_folder(name: str, parent_id: str) -> str:
    """Restituisce l'ID di una cartella esistente o la crea."""

    query = (
        f"'{parent_id}' in parents and name='{name}' and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    result = (
        drive_service.files()
        .list(q=query, fields="files(id)", spaces="drive")
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
        drive_service.files()
        .create(body=folder_metadata, fields="id")
        .execute()
    )
    return folder["id"]


def download_from_drive(file_id: str) -> bytes:
    """Scarica il contenuto di un file da Drive e lo restituisce come bytes."""

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh.read()
