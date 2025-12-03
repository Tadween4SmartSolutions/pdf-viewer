import os
import fitz  # PyMuPDF
from flask import Flask, render_template, send_file, request, jsonify, flash, redirect, url_for, abort
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from config import config
from models import db, User, PDFFile, Share
from auth import auth_bp
from forms import PDFUploadForm, SearchForm, ShareForm
import secrets
from PIL import Image
import io
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# PDF Processor (existing code remains the same)
class PDFProcessor:
    def __init__(self, app):
        self.app = app
        self.ensure_directories()
    
    def ensure_directories(self):
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(self.app.config['THUMBNAIL_FOLDER'], exist_ok=True)
    
    def generate_thumbnail(self, pdf_path, output_path):
        """Generate thumbnail from first page of PDF"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            
            # Process image with PIL
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail(self.app.config['THUMBNAIL_SIZE'])
            img.save(output_path, 'PNG')
            doc.close()
            return True
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            return False
    
    def extract_text(self, pdf_path, max_pages=10):
        """Extract text from PDF for search"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for i, page in enumerate(doc):
                if i >= max_pages:  # Limit pages for performance
                    break
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Text extraction failed: {e}")
            return ""
    
    def get_pdf_metadata(self, pdf_path):
        """Extract PDF metadata"""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            page_count = len(doc)
            doc.close()
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'page_count': page_count
            }
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {'page_count': 0}

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # PDF processor
    pdf_processor = PDFProcessor(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    
    # Main routes (existing routes remain the same until we add new ones)
    @app.route('/')
    def index():
        page = request.args.get('page', 1, type=int)
        search_form = SearchForm()
        
        # Get public PDFs or user's private PDFs
        if current_user.is_authenticated:
            pdfs_query = PDFFile.query.filter(
                (PDFFile.is_public == True) | (PDFFile.user_id == current_user.id)
            )
        else:
            pdfs_query = PDFFile.query.filter_by(is_public=True)
        
        # Pagination
        pdfs = pdfs_query.order_by(PDFFile.upload_date.desc()).paginate(
            page=page, per_page=app.config['PDFS_PER_PAGE'], error_out=False
        )
        
        return render_template('index.html', pdfs=pdfs, search_form=search_form)

    @app.route('/pdfs/<path:filename>')
    def serve_pdf(filename):
        """Serve a PDF by stored filename."""
        pdf = PDFFile.query.filter_by(filename=filename).first_or_404()
        # ensure file exists on disk
        if not os.path.exists(pdf.file_path):
            abort(404)
        return send_file(pdf.file_path, as_attachment=False)

    @app.route('/thumbnails/<path:filename>')
    def serve_thumbnail(filename):
        """Serve a thumbnail image from the thumbnails folder."""
        thumb_folder = app.config.get('THUMBNAIL_FOLDER')
        if not thumb_folder:
            abort(404)
        path = os.path.join(thumb_folder, filename)
        if not os.path.exists(path):
            abort(404)
        return send_file(path, mimetype='image/png', as_attachment=False)
    
    # ... existing routes (search, upload, serve_pdf, serve_thumbnail, pdf_preview, api/pdfs, admin) ...
    
    # NEW SHARE ROUTES
    
    @app.route('/share/<int:pdf_id>', methods=['GET', 'POST'])
    @login_required
    def share_pdf(pdf_id):
        pdf_file = PDFFile.query.get_or_404(pdf_id)
        
        # Check ownership
        if pdf_file.user_id != current_user.id and not current_user.is_admin:
            flash('You can only share your own files', 'error')
            return redirect(url_for('index'))
        
        form = ShareForm()
        
        if form.validate_on_submit():
            # Calculate expiration date based on form input
            expires_at = None
            
            if form.expiration_type.data == 'never':
                expires_at = datetime.utcnow() + timedelta(days=365*10)  # 10 years
            elif form.expiration_type.data == 'date':
                expires_at = form.expires_at.data
            elif form.expiration_type.data == 'days':
                expires_at = datetime.utcnow() + timedelta(days=form.days_valid.data)
            elif form.expiration_type.data == 'downloads':
                expires_at = datetime.utcnow() + timedelta(days=365)  # 1 year default
                max_access_count = form.max_access_count.data
            else:
                expires_at = datetime.utcnow() + timedelta(days=7)  # Default 7 days
            
            # Generate unique share token
            share_token = secrets.token_urlsafe(16)
            
            # Create share record
            share = Share(
                share_token=share_token,
                pdf_file_id=pdf_id,
                user_id=current_user.id,
                expires_at=expires_at,
                max_access_count=form.max_access_count.data if form.expiration_type.data == 'downloads' else 0,
                allow_download=form.allow_download.data,
                password_hash=generate_password_hash(form.password.data) if form.password.data else None,
                description=form.description.data
            )
            
            db.session.add(share)
            db.session.commit()
            
            share_url = share.get_share_url(request.host_url)
            flash(f'Share link created successfully!', 'success')
            return render_template('share_created.html', 
                                 share=share, 
                                 share_url=share_url, 
                                 pdf_file=pdf_file)
        
        # Set default expiration date
        form.expires_at.data = datetime.utcnow() + timedelta(days=7)
        
        return render_template('share.html', form=form, pdf_file=pdf_file)
    
    @app.route('/shared/<share_token>', methods=['GET', 'POST'])
    def shared_pdf(share_token):
        share = Share.query.filter_by(share_token=share_token).first_or_404()
        
        # Check if share is active
        if not share.is_active():
            if share.is_expired():
                return render_template('share_expired.html'), 410
            else:
                return render_template('share_limit_reached.html'), 410
        
        # Check password if set
        if share.password_hash:
            if request.method == 'POST':
                password = request.form.get('password')
                if password and check_password_hash(share.password_hash, password):
                    # Password correct, show the file
                    share.record_access()
                    return render_template('shared_view.html', share=share)
                else:
                    flash('Invalid password', 'error')
            return render_template('share_password.html', share=share)
        
        # No password required, show the file
        if request.method == 'GET':
            share.record_access()
        
        return render_template('shared_view.html', share=share)
    
    @app.route('/shared/<share_token>/download')
    def shared_download(share_token):
        share = Share.query.filter_by(share_token=share_token).first_or_404()
        
        # Check if share is active
        if not share.is_active():
            abort(410)
        
        # Check if download is allowed
        if not share.allow_download:
            flash('Download is not allowed for this shared file', 'error')
            return redirect(url_for('shared_pdf', share_token=share_token))
        
        share.record_access()
        return send_file(share.pdf_file.file_path, 
                        as_attachment=True, 
                        download_name=share.pdf_file.original_filename)
    
    @app.route('/shared/<share_token>/preview')
    def shared_preview(share_token):
        share = Share.query.filter_by(share_token=share_token).first_or_404()
        
        if not share.is_active():
            abort(410)
        
        return send_file(share.pdf_file.file_path, as_attachment=False)
    
    @app.route('/manage-shares')
    @login_required
    def manage_shares():
        shares = Share.query.filter_by(user_id=current_user.id)\
                          .order_by(Share.created_at.desc())\
                          .all()
        
        active_shares = [s for s in shares if s.is_active()]
        expired_shares = [s for s in shares if not s.is_active()]
        
        return render_template('manage_shares.html', 
                             active_shares=active_shares,
                             expired_shares=expired_shares)
    
    @app.route('/share/<int:share_id>/delete', methods=['POST'])
    @login_required
    def delete_share(share_id):
        share = Share.query.get_or_404(share_id)
        
        # Check ownership
        if share.user_id != current_user.id and not current_user.is_admin:
            flash('Access denied', 'error')
            return redirect(url_for('manage_shares'))
        
        db.session.delete(share)
        db.session.commit()
        
        flash('Share link deleted successfully', 'success')
        return redirect(url_for('manage_shares'))
    
    @app.route('/api/share/<int:pdf_id>', methods=['POST'])
    @login_required
    def api_create_share(pdf_id):
        """API endpoint for creating shares"""
        pdf_file = PDFFile.query.get_or_404(pdf_id)
        
        if pdf_file.user_id != current_user.id and not current_user.is_admin:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=data.get('days_valid', 7))
        
        # Generate share token
        share_token = secrets.token_urlsafe(16)
        
        share = Share(
            share_token=share_token,
            pdf_file_id=pdf_id,
            user_id=current_user.id,
            expires_at=expires_at,
            max_access_count=data.get('max_access_count', 0),
            allow_download=data.get('allow_download', True),
            description=data.get('description', '')
        )
        
        db.session.add(share)
        db.session.commit()
        
        return jsonify(share.to_dict())
    
    # Helper function
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    # Context processors
    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)