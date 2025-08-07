# utils/drive_uploader.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scope per upload “file.only”
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Inizializza le credenziali e il servizio Drive
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=creds)

def upload_to_drive(local_path: str, drive_folder_id: str) -> dict:
    """
    Carica il file su Google Drive nella cartella specificata.
    Ritorna il dict con 'id' e 'webViewLink'.
    """
    file_metadata = {
        'name': os.path.basename(local_path),
        'parents': [drive_folder_id]
    }
    media = MediaFileUpload(local_path, mimetype='application/pdf')
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    return file
