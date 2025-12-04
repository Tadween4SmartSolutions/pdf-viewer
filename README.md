# PDF Viewer (DeepSeek fork)

A lightweight Flask-based PDF viewing and sharing app with DB-backed file records, thumbnail generation, and an integrated canvas-based PDF preview powered by PDF.js.

This repository contains utilities to import PDFs on disk into the database, generate thumbnails (via PyMuPDF), and an in-browser preview implemented with PDF.js.

## Contents
- `app.py` — Flask app factory and route definitions.
- `models.py` — SQLAlchemy models (`User`, `PDFFile`, `Share`).
- `templates/` — Jinja2 templates (including `base.html` and `index.html`).
- `static/js/` — client-side JS. `pdfjs_viewer.js` is a minimal wrapper that loads PDF.js from CDN.
- `tools/import_pdfs.py` — script to import PDFs from disk into the DB and (re)generate thumbnails.
- `pdfs/thumbnails/` — generated thumbnail PNGs.

## Prerequisites
- macOS / Linux / Windows with Python 3.10+ recommended
- A virtual environment (recommended)
- System packages / libraries required by some imaging libs (usually available by default on macOS)

## Setup
1. Create and activate a virtualenv (example):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

Note: There was a common conflict with a small PyPI package named `fitz`. Ensure `PyMuPDF` is installed and any stray `fitz` package is uninstalled:

```bash
pip uninstall -y fitz || true
pip install --upgrade PyMuPDF
```

3. Initialize the database (if not already):

```bash
# sample commands — adjust to your migration workflow
flask db upgrade
# or
python create-admin.py
```

## Import PDFs already on disk
Files sitting in the `pdfs/` folder are not shown until they have rows in the DB. Use the importer tool to scan a folder and create DB rows (and generate thumbnails/text):

```bash
python tools/import_pdfs.py pdfs --force
```

Options:
- `--force` will update existing DB rows (re-generate thumbnails / text). Without `--force` the importer will only add missing rows.

Generated thumbnails are stored under `pdfs/thumbnails/` and `PDFFile.thumbnail_path` refers to that location.

## Running the app
Set the FLASK app and run the server (or use whichever run command you prefer):

```bash
export FLASK_APP=app.py
flask run
# or
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## Preview (PDF.js integration)
The preview modal uses `static/js/pdfjs_viewer.js` which lazy-loads PDF.js from CDN (Cloudflare CDN). This provides canvas-based rendering (better zoom and page control than an iframe).

Controls in the preview modal:
- Prev / Next arrows — navigate pages
- `-` / `+` — zoom out / zoom in
- `Reset` — reset zoom

If you need offline usage or want to vendor PDF.js, see `docs/PDFJS_INTEGRATION.md` for instructions.

## Key Files to Know
- `templates/index.html` — preview modal markup and toolbar.
- `static/js/pdfjs_viewer.js` — wrapper that loads PDF.js and exposes `pdfjsViewer.load(url)` plus navigation/zoom methods.
- `static/js/script.js` — integrates page UI with the pdfjsViewer API.
- `tools/import_pdfs.py` — importer script.
- `app.py` — server routes `GET /pdf/<int:id>` and thumbnail serving.

## Troubleshooting
- `module 'fitz' has no attribute 'open'`: uninstall any `fitz` package and install `PyMuPDF` (see above).
- PDF.js cannot load PDF: check that `/pdf/<id>` or `/pdfs/<filename>` routes return the PDF bytes with correct Content-Type and that the server allows the current session to fetch the resource.
- If PDF thumbnails fail to generate, confirm `PyMuPDF` is installed in the same environment used to run the importer.

## Next improvements
- Vendor PDF.js locally under `static/vendor/pdfjs/` for offline usage.
- Add text-selection/search support via PDF.js text layer.
- Improve toolbar UI/keyboard navigation and add a full-featured PDF.js viewer page.

If you'd like, I can vendor PDF.js into the repo and add keyboard controls next.
