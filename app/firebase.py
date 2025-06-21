import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from app.config import get_settings

settings = get_settings()

# Initialize Firebase app only if service account path is provided
firebase_initialized = False
if settings.firebase_service_account_path and settings.firebase_service_account_path.strip():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(settings.firebase_service_account_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print("✅ Firebase Admin SDK initialized.")
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            firebase_initialized = False
else:
    print("⚠️ FIREBASE_SERVICE_ACCOUNT_PATH is not set. Firebase authentication will not be configured.")


def verify_firebase_token(id_token: str) -> dict:
    if not firebase_initialized:
        raise Exception("Firebase not initialized")
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise e 