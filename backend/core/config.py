

"""Application Configuration"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


# class Settings(BaseSettings):
#     # App
#     APP_NAME: str = "Invoice OCR System"
#     APP_VERSION: str = "1.0.0"
#     DEBUG: bool = False
#     SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
#     ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
class Settings(BaseSettings):
    APP_NAME: str = "OCR API"
    DEBUG: bool = True
    OCR_PROVIDER: str = "tesseract"
    APP_VERSION: str = "1.0.0"
    # DEBUG: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres.rknmuphdrjptswxbtpqs:"
        "Suraj%40supabase%23123@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]

    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "/tmp/invoice_uploads"
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".pdf"]

    # OCR Provider: "easyocr" | "paddleocr" | "google" | "azure" | "aws"
    #
    # EasyOCR is the recommended default:
    #   - Works on Python 3.11 + Windows without version conflicts
    #   - Has native models for: en, hi, mr (via hi), gu, ta, te
    #
    # PaddleOCR note:
    #   - No Gujarati (gu) model — falls back to English
    #   - Better accuracy for Hindi/Tamil/Telugu in clean images
    #   - Use paddlepaddle==3.0.0 + paddleocr==2.9.1 on Python 3.11+
    # OCR_PROVIDER: str = "easyocr"
    OCR_PROVIDER="tesseract"

    # GPU flag used by both EasyOCR and PaddleOCR
    PADDLE_USE_GPU: bool = False

    # Google Vision (optional)
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Azure Form Recognizer (optional)
    AZURE_FORM_RECOGNIZER_ENDPOINT: str = ""
    AZURE_FORM_RECOGNIZER_KEY: str = ""

    # AWS Textract (optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Rate Limiting
    RATE_LIMIT: str = "100/minute"

    @field_validator("UPLOAD_DIR")
    @classmethod
    def create_upload_dir(cls, v):
        os.makedirs(v, exist_ok=True)
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()