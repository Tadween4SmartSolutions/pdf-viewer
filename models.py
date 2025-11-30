from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import os
import secrets

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with PDF files
    pdf_files = db.relationship('PDFFile', backref='owner', lazy=True)
    shares = db.relationship('Share', backref='owner', lazy=True)

class PDFFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    thumbnail_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer, nullable=False)
    page_count = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Searchable content (extracted text)
    extracted_text = db.Column(db.Text)
    
    # Metadata
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    
    # User who uploaded the file
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Privacy settings
    is_public = db.Column(db.Boolean, default=True)
    
    # Relationships
    shares = db.relationship('Share', backref='pdf_file', lazy=True, cascade='all, delete-orphan')
    
    def get_thumbnail_url(self):
        if self.thumbnail_path and os.path.exists(self.thumbnail_path):
            return f'/thumbnails/{os.path.basename(self.thumbnail_path)}'
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'page_count': self.page_count,
            'upload_date': self.upload_date.isoformat(),
            'title': self.title,
            'author': self.author,
            'thumbnail_url': self.get_thumbnail_url(),
            'is_public': self.is_public,
            'share_count': len(self.shares)
        }

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    share_token = db.Column(db.String(32), unique=True, nullable=False, index=True)
    pdf_file_id = db.Column(db.Integer, db.ForeignKey('pdf_file.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Share settings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    max_access_count = db.Column(db.Integer, default=0)  # 0 = unlimited
    current_access_count = db.Column(db.Integer, default=0)
    
    # Access tracking
    last_accessed = db.Column(db.DateTime)
    
    # Share options
    allow_download = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(255))  # Optional password protection
    
    # Share metadata
    description = db.Column(db.String(500))
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def is_access_limit_reached(self):
        return self.max_access_count > 0 and self.current_access_count >= self.max_access_count
    
    def is_active(self):
        return not self.is_expired() and not self.is_access_limit_reached()
    
    def record_access(self):
        self.current_access_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def get_share_url(self, base_url):
        return f"{base_url}/shared/{self.share_token}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'share_token': self.share_token,
            'pdf_file': self.pdf_file.to_dict(),
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'max_access_count': self.max_access_count,
            'current_access_count': self.current_access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'allow_download': self.allow_download,
            'is_active': self.is_active(),
            'description': self.description,
            'share_url': self.get_share_url(request.host_url if 'request' in globals() else '')
        }