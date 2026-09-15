import os

from dotenv import load_dotenv

load_dotenv()


def normalize_database_url(url: str) -> str:
    """Render/Supabase 有时提供 postgres://，SQLAlchemy 需要 postgresql://。"""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///safecheck.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "30 per minute"
    MAX_SCAM_TEXT_LENGTH = 5000
    MAX_FEEDBACK_LENGTH = 500
