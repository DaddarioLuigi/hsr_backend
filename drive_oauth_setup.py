import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

_SCOPES_DEFAULT = 'https://www.googleapis.com/auth/drive'
SCOPES = [s.strip() for s in (os.getenv('GOOGLE_DRIVE_SCOPES', _SCOPES_DEFAULT)).split(',') if s.strip()]

if __name__ == "__main__":
    secrets_path = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "client_secret.json")
    token_path = os.getenv("GOOGLE_OAUTH_TOKEN_PATH", "token.json")
    flow_mode = (os.getenv("OAUTH_FLOW") or "server").lower()  # 'server' | 'console'
    redirect_port = int(os.getenv("OAUTH_REDIRECT_PORT", "0"))

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if flow_mode == "console":
                flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
                creds = flow.run_console()
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
                    creds = flow.run_local_server(port=redirect_port)
                except Exception:
                    # Fallback automatico a console se il server locale non riesce
                    flow = InstalledAppFlow.from_client_secrets_file(secrets_path, SCOPES)
                    creds = flow.run_console()
        with open(token_path, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
    print(f"Saved token to {token_path}") 