import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from app.config import get_settings

settings = get_settings()

# Initialize Firebase app only once
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.firebase_service_account_path)
    firebase_admin.initialize_app(cred)


def verify_firebase_token(id_token: str) -> dict:
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise e 