#!/usr/bin/env python3
import os
import sys
import uuid

# make project root importable when script is run from tools/
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from app import create_app, PDFProcessor
from models import db, PDFFile, User
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()

def ensure_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    return admin

with app.app_context():
    upload_folder = app.config.get('UPLOAD_FOLDER')
    # allow optional override: `tools/import_pdfs.py <path-to-folder> [--force]`
    import sys as _sys
    force = ('--force' in _sys.argv) or ('-f' in _sys.argv)
    # first non-flag arg can be the folder
    args = [a for a in _sys.argv[1:] if not a.startswith('-')]
    if len(args) > 0 and args[0]:
        upload_folder = args[0]
    thumb_folder = app.config.get('THUMBNAIL_FOLDER')
    if not upload_folder:
        print('No UPLOAD_FOLDER configured in app. Aborting.')
        raise SystemExit(1)

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(thumb_folder, exist_ok=True)

    pdf_processor = PDFProcessor(app)

    user = User.query.first() or ensure_admin()

    added = 0
    updated = 0
    for fname in os.listdir(upload_folder):
        if not fname.lower().endswith('.pdf'):
            continue
        file_path = os.path.join(upload_folder, fname)
        # check DB by filename
        existing = PDFFile.query.filter_by(filename=fname).first()
        if existing and not force:
            print(f'Skipping existing DB entry for {fname} (use --force to update)')
            continue

        # Generate thumbnail
        thumb_name = f"{uuid.uuid4().hex}.png"
        thumb_path = os.path.join(thumb_folder, thumb_name)
        try:
            ok = pdf_processor.generate_thumbnail(file_path, thumb_path)
        except Exception as e:
            print(f'Failed to generate thumbnail for {fname}: {e}')
            ok = False

        metadata = pdf_processor.get_pdf_metadata(file_path)

        file_size = os.path.getsize(file_path)

        if existing:
            # update existing record
            existing.original_filename = fname
            existing.file_path = os.path.abspath(file_path)
            existing.thumbnail_path = os.path.abspath(thumb_path) if ok else existing.thumbnail_path
            existing.file_size = file_size
            existing.page_count = metadata.get('page_count', existing.page_count)
            existing.extracted_text = pdf_processor.extract_text(file_path)
            existing.title = metadata.get('title') or existing.title
            existing.author = metadata.get('author') or existing.author
            existing.subject = metadata.get('subject') or existing.subject
            db.session.add(existing)
            updated += 1
            print(f'Updated DB entry for {fname}')
        else:
            pdf = PDFFile(
                filename=fname,
                original_filename=fname,
                file_path=os.path.abspath(file_path),
                thumbnail_path=os.path.abspath(thumb_path) if ok else None,
                file_size=file_size,
                page_count=metadata.get('page_count', None),
                extracted_text=pdf_processor.extract_text(file_path),
                title=metadata.get('title') or '',
                author=metadata.get('author') or '',
                subject=metadata.get('subject') or '',
                user_id=user.id,
                is_public=True,
                upload_date=datetime.utcnow()
            )
            db.session.add(pdf)
            added += 1
            print(f'Added DB entry for {fname}')

    if added or updated:
        db.session.commit()
    print(f'Done. Added {added} files, updated {updated} files.')
