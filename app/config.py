import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{BASE_DIR / "data" / "procure.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    PORT = int(os.environ.get('PORT', 5001))

class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = True  # keep on even in dev

config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig,
}
