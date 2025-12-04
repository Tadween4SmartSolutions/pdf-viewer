// Minimal PDF.js wrapper that loads the library from CDN if needed
// Exposes a simple API: pdfjsViewer.load(url) -> Promise, pdfjsViewer.renderPage(n)

(function(window){
    const CDN_PDFJS = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js';
    const CDN_WORKER = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';

    const state = {
        pdf: null,
        currentPage: 1,
        scale: 1.0,
        canvas: null,
        ctx: null
    };

    function ensurePdfJs() {
        return new Promise((resolve, reject) => {
            if (window.pdfjsLib) return resolve(window.pdfjsLib);
            const s = document.createElement('script');
            s.src = CDN_PDFJS;
            s.onload = () => {
                if (!window.pdfjsLib) return reject(new Error('pdfjs failed to load'));
                resolve(window.pdfjsLib);
            };
            s.onerror = () => reject(new Error('Failed to load pdf.js from CDN'));
            document.head.appendChild(s);
        });
    }

    function initCanvas() {
        state.canvas = document.getElementById('pdfCanvas');
        if (!state.canvas) {
            console.warn('pdfCanvas not found in DOM');
            return;
        }
        state.ctx = state.canvas.getContext('2d');
    }

    async function load(url) {
        await ensurePdfJs();
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = CDN_WORKER;
        initCanvas();
        return new Promise((resolve, reject) => {
            const loadingTask = window.pdfjsLib.getDocument(url);
            loadingTask.promise.then(pdf => {
                state.pdf = pdf;
                state.currentPage = 1;
                state.scale = 1.0;
                // render first page
                renderPage(state.currentPage).then(() => resolve({page_count: pdf.numPages})).catch(reject);
            }).catch(reject);
        });
    }

    function renderPage(pageNum) {
        return new Promise((resolve, reject) => {
            if (!state.pdf) return reject(new Error('No PDF loaded'));
            state.pdf.getPage(pageNum).then(page => {
                const viewport = page.getViewport({scale: state.scale});
                // set canvas size to match viewport (device pixels considered)
                const outputScale = window.devicePixelRatio || 1;
                state.canvas.width = Math.floor(viewport.width * outputScale);
                state.canvas.height = Math.floor(viewport.height * outputScale);
                state.canvas.style.width = Math.floor(viewport.width) + 'px';
                state.canvas.style.height = Math.floor(viewport.height) + 'px';

                const transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null;
                const renderContext = {
                    canvasContext: state.ctx,
                    viewport: viewport,
                    transform: transform
                };
                const renderTask = page.render(renderContext);
                renderTask.promise.then(() => {
                    resolve();
                }).catch(reject);
            }).catch(reject);
        });
    }

    function nextPage() {
        if (!state.pdf) return;
        if (state.currentPage < state.pdf.numPages) {
            state.currentPage++;
            return renderPage(state.currentPage);
        }
        return Promise.resolve();
    }

    function prevPage() {
        if (!state.pdf) return;
        if (state.currentPage > 1) {
            state.currentPage--;
            return renderPage(state.currentPage);
        }
        return Promise.resolve();
    }

    function goToPage(n) {
        if (!state.pdf) return Promise.reject(new Error('No PDF loaded'));
        n = Math.max(1, Math.min(n, state.pdf.numPages));
        state.currentPage = n;
        return renderPage(n);
    }

    function zoomIn() {
        state.scale = +(state.scale + 0.25).toFixed(2);
        return renderPage(state.currentPage);
    }

    function zoomOut() {
        state.scale = Math.max(0.25, +(state.scale - 0.25).toFixed(2));
        return renderPage(state.currentPage);
    }

    function resetZoom() {
        state.scale = 1.0;
        return renderPage(state.currentPage);
    }

    window.pdfjsViewer = {
        load,
        renderPage: renderPage,
        nextPage,
        prevPage,
        goToPage,
        zoomIn,
        zoomOut,
        resetZoom,
        getState: () => ({ pdf: state.pdf, currentPage: state.currentPage, scale: state.scale })
    };

})(window);
