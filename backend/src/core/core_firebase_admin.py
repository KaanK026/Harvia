import firebase_admin
from firebase_admin import credentials, firestore, storage
from backend.src.core.config import FIREBASE_SERVICE_ACCOUNT_PATH, FIREBASE_STORAGE_BUCKET
from backend.src.utils.logger import get_logger
from PIL import Image
import io

logger = get_logger(__name__)


def initialize_firebase():
    """Initializes the Firebase Admin SDK if not already initialized."""
    if not firebase_admin._apps:
        try:
            if FIREBASE_SERVICE_ACCOUNT_PATH.exists():
                cred = credentials.Certificate(str(FIREBASE_SERVICE_ACCOUNT_PATH))
                firebase_admin.initialize_app(cred, {
                    'storageBucket': FIREBASE_STORAGE_BUCKET
                })
                logger.info("Firebase Admin initialized with service account., Bucket loaded")
            else:
                logger.error("Service account file not found at: %s", FIREBASE_SERVICE_ACCOUNT_PATH)
                firebase_admin.initialize_app({
                    'storageBucket': FIREBASE_STORAGE_BUCKET
                })
                logger.warning("Firebase Admin initialized with default credentials.")
        except Exception as e:
            logger.warning("Firebase Admin init failed: %s", e)


# Initialize on import
initialize_firebase()

# Firestore client
db = firestore.client() if firebase_admin._apps else None

# Storage bucket client
bucket = storage.bucket() if firebase_admin._apps else None


def upload_session_image(uid: str, session_id: str, image_bytes: bytes, filename: str):
    if not bucket:
        raise RuntimeError("Firebase Storage bucket not initialized")

    blob_path = f"sessions/{uid}/{session_id}/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")
    logger.info("Uploaded image to %s", blob_path)


def download_session_image(uid: str, session_id: str, filename: str) -> bytes:
    if not bucket:
        raise RuntimeError("Firebase Storage bucket not initialized")

    blob_path = f"sessions/{uid}/{session_id}/{filename}"
    blob = bucket.blob(blob_path)

    if not blob.exists():
        raise FileNotFoundError(f"No image found at {blob_path}")

    image_bytes = blob.download_as_bytes()
    logger.info("Downloaded image from %s", blob_path)
    return image_bytes


