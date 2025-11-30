import os
from flask import Flask, render_template, send_file, request, jsonify
import glob

app = Flask(__name__)

# Configuration
app.config['PDF_FOLDER'] = 'pdfs'
app.config['MAX_PREVIEW_PAGES'] = 3

def get_pdf_files():
    """Get all PDF files from the pdfs folder"""
    pdf_path = os.path.join(app.config['PDF_FOLDER'], '*.pdf')
    pdf_files = glob.glob(pdf_path)
    
    files_info = []
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        file_size = os.path.getsize(pdf_file)
        files_info.append({
            'name': filename,
            'path': pdf_file,
            'size': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2)
        })
    
    return files_info

@app.route('/')
def index():
    """Main page showing PDF files"""
    pdf_files = get_pdf_files()
    return render_template('index.html', pdf_files=pdf_files)

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    """Serve PDF file"""
    pdf_path = os.path.join(app.config['PDF_FOLDER'], filename)
    
    if not os.path.exists(pdf_path):
        return "File not found", 404
    
    return send_file(pdf_path, as_attachment=False)

@app.route('/preview/<filename>')
def pdf_preview(filename):
    """Generate PDF preview (first few pages)"""
    pdf_path = os.path.join(app.config['PDF_FOLDER'], filename)
    
    if not os.path.exists(pdf_path):
        return "File not found", 404
    
    # For a production app, you might want to generate actual preview images
    # For this example, we'll just return the file info
    file_info = {
        'name': filename,
        'path': pdf_path,
        'size': os.path.getsize(pdf_path)
    }
    
    return jsonify(file_info)

@app.route('/api/pdfs')
def api_pdfs():
    """API endpoint to get PDF files list"""
    pdf_files = get_pdf_files()
    return jsonify(pdf_files)

if __name__ == '__main__':
    # Create pdfs folder if it doesn't exist
    if not os.path.exists(app.config['PDF_FOLDER']):
        os.makedirs(app.config['PDF_FOLDER'])
        print(f"Created {app.config['PDF_FOLDER']} folder. Please add some PDF files.")
    
    app.run(debug=True, port=5000)