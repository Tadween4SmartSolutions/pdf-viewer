// Search functionality
function searchPDFs() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const pdfCards = document.querySelectorAll('.pdf-card');
    
    pdfCards.forEach(card => {
        const title = card.querySelector('.pdf-title').textContent.toLowerCase();
        if (title.includes(filter)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// Modal functionality
const modal = document.getElementById('previewModal');
const closeBtn = document.querySelector('.close');
// PDF.js viewer will render into #pdfCanvas
// const pdfPreview removed (we use pdfjsViewer)
const openPdfLink = document.getElementById('openPdfLink');
const previewTitle = document.getElementById('previewTitle');

// Open preview modal
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('preview-btn') || 
        e.target.parentElement.classList.contains('preview-btn')) {
        
        const btn = e.target.classList.contains('preview-btn') ? 
                   e.target : e.target.parentElement;
        const filename = btn.getAttribute('data-filename');
        const pdfId = btn.getAttribute('data-pdf-id');

        // Prefer advanced preview when pdf id is available
        if (pdfId) {
            openAdvancedPreview(pdfId);
        } else {
            openPreview(filename);
        }
    }
});

function openPreview(filename) {
    const pdfUrl = `/pdf/${encodeURIComponent(filename)}`;
    previewTitle.textContent = `Preview: ${filename}`;
    openPdfLink.href = pdfUrl;
    modal.style.display = 'block';
    showSpinner();

    // Use pdfjsViewer to load and render PDF into canvas
    if (window.pdfjsViewer && typeof window.pdfjsViewer.load === 'function') {
        window.pdfjsViewer.load(pdfUrl)
            .then(info => {
                hideSpinner();
                // reset zoom
                if (window.pdfjsViewer && window.pdfjsViewer.resetZoom) window.pdfjsViewer.resetZoom();
                updatePageNavigation(info.page_count);
            })
            .catch(err => {
                hideSpinner();
                console.error('PDF.js load error', err);
                alert('Failed to load PDF preview. Open full PDF instead.');
            });
    } else {
        hideSpinner();
        alert('PDF viewer not available');
    }
}

function closePreview() {
    modal.style.display = 'none';
}

closeBtn.addEventListener('click', closePreview);

window.addEventListener('click', function(e) {
    if (e.target === modal) {
        closePreview();
    }
});

// Hover preview functionality
const hoverPreview = document.getElementById('hoverPreview');
let hoverTimeout;

document.addEventListener('mouseover', function(e) {
    const target = e.target;
    
    // Check if hovering over PDF action buttons
    if (target.classList.contains('btn') || 
        target.parentElement.classList.contains('btn')) {
        
        const btn = target.classList.contains('btn') ? target : target.parentElement;
        const pdfCard = btn.closest('.pdf-card');
        const filename = pdfCard ? pdfCard.getAttribute('data-filename') : 'PDF File';
        
        clearTimeout(hoverTimeout);
        
        hoverTimeout = setTimeout(() => {
            showHoverPreview(e.clientX, e.clientY, filename, btn.classList.contains('btn-primary'));
        }, 500);
    }
});

document.addEventListener('mouseout', function(e) {
    const target = e.target;
    
    if (target.classList.contains('btn') || 
        target.parentElement.classList.contains('btn')) {
        clearTimeout(hoverTimeout);
        hideHoverPreview();
    }
});

document.addEventListener('mousemove', function(e) {
    if (hoverPreview.style.display === 'block') {
        hoverPreview.style.left = (e.clientX + 15) + 'px';
        hoverPreview.style.top = (e.clientY + 15) + 'px';
    }
});

function showHoverPreview(x, y, filename, isOpenButton) {
    const fileNameElement = document.getElementById('previewFileName');
    const previewContent = hoverPreview.querySelector('.preview-content');
    
    fileNameElement.textContent = filename;
    
    if (isOpenButton) {
        previewContent.innerHTML = '<p>Click to open this PDF in a new tab</p>';
    } else {
        previewContent.innerHTML = '<p>Click to preview this PDF in a modal</p>';
    }
    
    hoverPreview.style.left = (x + 15) + 'px';
    hoverPreview.style.top = (y + 15) + 'px';
    hoverPreview.style.display = 'block';
}

function hideHoverPreview() {
    hoverPreview.style.display = 'none';
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closePreview();
    }
});
// Enhanced search with debouncing
let searchTimeout;
function searchPDFs() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const query = document.getElementById('searchInput').value;
        if (query.length >= 2 || query.length === 0) {
            // Perform search via AJAX or form submission
            window.location.href = `/search?q=${encodeURIComponent(query)}&in=all`;
        }
    }, 500);
}

// File upload progress
function setupFileUpload() {
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileSize = (file.size / (1024 * 1024)).toFixed(2);
                if (fileSize > 50) {
                    alert('File size must be less than 50MB');
                    e.target.value = '';
                }
            }
        });
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupFileUpload();
    
    // Auto-hide flash messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'all 0.3s ease';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});

// Advanced preview with page navigation
let currentPdfId = null;
let currentPage = 1;

function openAdvancedPreview(pdfId) {
    currentPdfId = pdfId;
    currentPage = 1;
    showSpinner();
    fetch(`/preview/${pdfId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                hideSpinner();
                alert(data.error);
                return;
            }

            document.getElementById('previewTitle').textContent = data.original_filename;
            document.getElementById('openPdfLink').href = `/pdf/${pdfId}`;
            // request PDF via PDF.js viewer
            modal.style.display = 'block';
            if (window.pdfjsViewer && typeof window.pdfjsViewer.load === 'function') {
                window.pdfjsViewer.load(`/pdf/${pdfId}`)
                    .then(info => {
                        hideSpinner();
                        if (window.pdfjsViewer && window.pdfjsViewer.resetZoom) window.pdfjsViewer.resetZoom();
                        updatePageNavigation(info.page_count);
                    })
                    .catch(err => {
                        hideSpinner();
                        console.error('PDF.js load error', err);
                        alert('Failed to load PDF preview.');
                    });
            } else {
                hideSpinner();
                alert('PDF viewer not available');
            }
        })
        .catch(error => {
            hideSpinner();
            console.error('Error loading preview:', error);
        });
}

function updatePageNavigation(totalPages) {
    // update page info and navigation buttons
    const pageInfo = document.getElementById('pageInfo');
    if (!pageInfo) return;
    // ask pdfjsViewer for current page if available
    let cur = currentPage;
    if (window.pdfjsViewer && window.pdfjsViewer.getState) {
        try { cur = window.pdfjsViewer.getState().currentPage || currentPage; } catch(e){}
    }
    pageInfo.textContent = `Page ${cur} of ${totalPages}`;
    // manage previous/next state via enabling/disabling toolbar buttons
}

function changePage(delta) {
    showSpinner();
    if (!window.pdfjsViewer) {
        hideSpinner();
        return;
    }
    const fn = delta > 0 ? window.pdfjsViewer.nextPage : window.pdfjsViewer.prevPage;
    if (typeof fn === 'function') {
        fn().then(() => {
            // update local tracker
            if (window.pdfjsViewer && window.pdfjsViewer.getState) {
                const s = window.pdfjsViewer.getState();
                currentPage = s.currentPage;
                updatePageNavigation(s.pdf ? s.pdf.numPages : null);
            }
            hideSpinner();
        }).catch(err => { hideSpinner(); console.error(err); });
    } else {
        hideSpinner();
    }
}

// Spinner helpers
function showSpinner() {
    const s = document.getElementById('previewSpinner');
    if (s) s.style.display = 'block';
}

function hideSpinner() {
    const s = document.getElementById('previewSpinner');
    if (s) s.style.display = 'none';
}

// Zoom handling (scale the iframe)
let currentZoom = 1;
function zoomIn() {
    if (window.pdfjsViewer && window.pdfjsViewer.zoomIn) {
        showSpinner();
        window.pdfjsViewer.zoomIn().then(() => hideSpinner()).catch(err => { hideSpinner(); console.error(err); });
    } else {
        currentZoom = +(currentZoom + 0.1).toFixed(2);
        applyZoom();
    }
}

function zoomOut() {
    if (window.pdfjsViewer && window.pdfjsViewer.zoomOut) {
        showSpinner();
        window.pdfjsViewer.zoomOut().then(() => hideSpinner()).catch(err => { hideSpinner(); console.error(err); });
    } else {
        currentZoom = Math.max(0.2, +(currentZoom - 0.1).toFixed(2));
        applyZoom();
    }
}

function resetZoom() {
    if (window.pdfjsViewer && window.pdfjsViewer.resetZoom) {
        showSpinner();
        window.pdfjsViewer.resetZoom().then(() => hideSpinner()).catch(err => { hideSpinner(); console.error(err); });
    } else {
        currentZoom = 1;
        applyZoom();
    }
}

function applyZoom() {
    const wrapper = document.querySelector('.preview-container-wrapper');
    const canvas = document.getElementById('pdfCanvas');
    if (canvas && wrapper) {
        canvas.style.transform = `scale(${currentZoom})`;
        canvas.style.transformOrigin = 'top left';
        // adjust wrapper scroll area if needed
        canvas.style.width = `${100 / currentZoom}%`;
        // height will be automatic based on canvas render
    }
}