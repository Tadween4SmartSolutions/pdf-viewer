from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import os

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
            'is_public': self.is_public
        }