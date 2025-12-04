import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PDF Configuration
    PDF_FOLDER = 'pdfs'
    UPLOAD_FOLDER = 'pdfs/user_uploads'
    THUMBNAIL_FOLDER = 'pdfs/thumbnails'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # Thumbnail Configuration
    THUMBNAIL_SIZE = (200, 280)
    MAX_PREVIEW_PAGES = 3
    
    # Search Configuration
    ENABLE_TEXT_SEARCH = True
    # LLM / Model configuration: set to empty string to disable LLM usage
    # Example: export DEFAULT_LLM=""  (disables); export DEFAULT_LLM="claude-haiku" (enables)
    DEFAULT_LLM = os.environ.get('DEFAULT_LLM', '')
    
    # Pagination
    PDFS_PER_PAGE = 12
    
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}