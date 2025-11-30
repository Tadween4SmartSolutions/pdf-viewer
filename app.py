import os
import fitz  # PyMuPDF
from flask import Flask, render_template, send_file, request, jsonify, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from config import config
from models import db, User, PDFFile
from auth import auth_bp
from forms import PDFUploadForm, SearchForm
import secrets
from PIL import Image
import io
from datetime import datetime

# PDF Processor
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
    
    # Main routes
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
    
    @app.route('/search')
    def search():
        query = request.args.get('q', '')
        search_in = request.args.get('in', 'all')
        page = request.args.get('page', 1, type=int)
        
        if not query:
            return redirect(url_for('index'))
        
        # Base query
        if current_user.is_authenticated:
            base_query = PDFFile.query.filter(
                (PDFFile.is_public == True) | (PDFFile.user_id == current_user.id)
            )
        else:
            base_query = PDFFile.query.filter_by(is_public=True)
        
        # Search logic
        if search_in in ['filename', 'all']:
            base_query = base_query.filter(
                PDFFile.original_filename.ilike(f'%{query}%') |
                PDFFile.title.ilike(f'%{query}%')
            )
        
        if search_in in ['content', 'all'] and app.config['ENABLE_TEXT_SEARCH']:
            base_query = base_query.filter(
                PDFFile.extracted_text.ilike(f'%{query}%')
            )
        
        pdfs = base_query.order_by(PDFFile.upload_date.desc()).paginate(
            page=page, per_page=app.config['PDFS_PER_PAGE'], error_out=False
        )
        
        return render_template('index.html', pdfs=pdfs, search_query=query, search_in=search_in)
    
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        form = PDFUploadForm()
        if form.validate_on_submit():
            file = form.file.data
            
            if not allowed_file(file.filename):
                flash('Only PDF files are allowed', 'error')
                return render_template('upload.html', form=form)
            
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = secrets.token_hex(16) + file_ext
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Process PDF
            metadata = pdf_processor.get_pdf_metadata(file_path)
            extracted_text = pdf_processor.extract_text(file_path)
            
            # Generate thumbnail
            thumbnail_filename = secrets.token_hex(16) + '.png'
            thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
            pdf_processor.generate_thumbnail(file_path, thumbnail_path)
            
            # Create PDF record
            pdf_file = PDFFile(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                thumbnail_path=thumbnail_path,
                file_size=os.path.getsize(file_path),
                page_count=metadata['page_count'],
                extracted_text=extracted_text,
                title=form.title.data or metadata['title'] or os.path.splitext(file.filename)[0],
                author=form.author.data or metadata['author'] or '',
                subject=form.subject.data or metadata['subject'] or '',
                user_id=current_user.id,
                is_public=form.is_public.data
            )
            
            db.session.add(pdf_file)
            db.session.commit()
            
            flash('PDF uploaded successfully!', 'success')
            return redirect(url_for('index'))
        
        return render_template('upload.html', form=form)
    
    @app.route('/pdf/<int:pdf_id>')
    def serve_pdf(pdf_id):
        pdf_file = PDFFile.query.get_or_404(pdf_id)
        
        # Check access
        if not pdf_file.is_public and (not current_user.is_authenticated or pdf_file.user_id != current_user.id):
            flash('Access denied', 'error')
            return redirect(url_for('auth.login'))
        
        return send_file(pdf_file.file_path, as_attachment=False)
    
    @app.route('/thumbnails/<filename>')
    def serve_thumbnail(filename):
        thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], filename)
        if os.path.exists(thumbnail_path):
            return send_file(thumbnail_path)
        else:
            # Return default thumbnail
            return send_file('static/images/default-thumbnail.png')
    
    @app.route('/preview/<int:pdf_id>')
    def pdf_preview(pdf_id):
        pdf_file = PDFFile.query.get_or_404(pdf_id)
        
        # Check access
        if not pdf_file.is_public and (not current_user.is_authenticated or pdf_file.user_id != current_user.id):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(pdf_file.to_dict())
    
    @app.route('/api/pdfs')
    def api_pdfs():
        page = request.args.get('page', 1, type=int)
        
        if current_user.is_authenticated:
            pdfs_query = PDFFile.query.filter(
                (PDFFile.is_public == True) | (PDFFile.user_id == current_user.id)
            )
        else:
            pdfs_query = PDFFile.query.filter_by(is_public=True)
        
        pdfs = pdfs_query.paginate(
            page=page, per_page=app.config['PDFS_PER_PAGE'], error_out=False
        )
        
        return jsonify({
            'pdfs': [pdf.to_dict() for pdf in pdfs.items],
            'total': pdfs.total,
            'pages': pdfs.pages,
            'current_page': page
        })
    
    @app.route('/admin')
    @login_required
    def admin():
        if not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        users = User.query.all()
        pdfs = PDFFile.query.all()
        return render_template('admin.html', users=users, pdfs=pdfs)
    
    # Helper function
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)