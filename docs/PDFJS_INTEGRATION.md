# PDF.js Integration Guide

This document explains the lightweight PDF.js integration added to this project, how it works, how to vendor PDF.js locally, and how to customize or extend the viewer.

## What was added
- `static/js/pdfjs_viewer.js`: a small wrapper that loads PDF.js from a CDN and exposes a simple API:
  - `pdfjsViewer.load(url)` -> Promise resolving to `{ page_count }` when the first page renders
  - `pdfjsViewer.nextPage()`, `pdfjsViewer.prevPage()`, `pdfjsViewer.goToPage(n)` -> Promises
  - `pdfjsViewer.zoomIn()`, `pdfjsViewer.zoomOut()`, `pdfjsViewer.resetZoom()` -> Promises
  - `pdfjsViewer.getState()` -> returns { pdf, currentPage, scale } (pdf is the underlying PDF.js PDFDocumentProxy)

- `templates/index.html` preview modal now contains a canvas (`#pdfCanvas`) where the viewer renders pages.
- `static/js/script.js` now uses `pdfjsViewer` (when available) to load PDFs for preview and to drive toolbar controls (prev/next/zoom/reset).

## How the wrapper works
- `pdfjs_viewer.js` lazy-loads `pdf.min.js` from the CDN and sets `GlobalWorkerOptions.workerSrc` to a CDN worker script.
- Once `pdfjsLib.getDocument(url)` resolves, the wrapper stores the `PDFDocumentProxy` and renders the requested page to the `#pdfCanvas` element using the `CanvasRenderingContext2D`.
- The wrapper performs pixel-ratio aware renders for crisp output on high-DPI displays.

## CDN details (defaults used)
- pdf.js: https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js
- pdf.worker.js: https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js

If you'd like to pin to a different version, modify the URLs in `static/js/pdfjs_viewer.js`.

## Vendor PDF.js locally (optional)
To avoid using the CDN, download the PDF.js distribution and place it under `static/vendor/pdfjs/`:

1. Download the latest stable release from the official repo: https://github.com/mozilla/pdf.js/releases
2. Copy `build/pdf.js` and `build/pdf.worker.js` into `static/vendor/pdfjs/`.
3. Edit `static/js/pdfjs_viewer.js` and change the `CDN_PDFJS` and `CDN_WORKER` constants to the local paths:

```js
const CDN_PDFJS = '/static/vendor/pdfjs/pdf.js';
const CDN_WORKER = '/static/vendor/pdfjs/pdf.worker.js';
```

4. If you prefer to serve them via a different path, ensure the `workerSrc` points to the correct URL.

## API usage examples
- Load a PDF URL:
```js
pdfjsViewer.load('/pdf/123').then(info => console.log('num pages', info.page_count));
```

- Go to next page:
```js
pdfjsViewer.nextPage();
```

- Zoom in:
```js
pdfjsViewer.zoomIn();
```

- Get current state:
```js
console.log(pdfjsViewer.getState());
```

## Debugging tips
- If PDFs don't render and you see CORS or fetch errors, verify the `/pdf/<id>` route returns the PDF bytes with `Content-Type: application/pdf` and that the same-origin policy isn't blocking the request.
- If pages render but appear fuzzy, check devicePixelRatio handling. The wrapper sets canvas pixel dimensions according to the device pixel ratio; if you change scale logic, adapt the transform accordingly.
- If the worker fails to load, confirm `pdf.worker.js` path is reachable by the browser. The worker path must be accessible from the browser (relative or absolute URL).

## Next steps / Enhancements
- Add a text layer for selectable/copyable text (requires extracting text positions or using PDF.js textLayer rendering).
- Integrate the full-featured PDF.js `web/viewer.html` if you want search, thumbnails, print, download, attachments, and an extensive toolbar out of the box.
- Add keyboard handlers for arrow keys, page up/down, and zoom shortcuts.

---

If you want, I can vendor PDF.js into `static/vendor/pdfjs/` and update the wrapper to use local files, and/or wire keyboard controls and a page input box in the toolbar. Tell me which you'd prefer next.