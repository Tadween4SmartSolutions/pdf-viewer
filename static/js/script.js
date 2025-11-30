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
const pdfPreview = document.getElementById('pdfPreview');
const openPdfLink = document.getElementById('openPdfLink');
const previewTitle = document.getElementById('previewTitle');

// Open preview modal
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('preview-btn') || 
        e.target.parentElement.classList.contains('preview-btn')) {
        
        const btn = e.target.classList.contains('preview-btn') ? 
                   e.target : e.target.parentElement;
        const filename = btn.getAttribute('data-filename');
        
        openPreview(filename);
    }
});

function openPreview(filename) {
    const pdfUrl = `/pdf/${filename}`;
    pdfPreview.src = pdfUrl;
    openPdfLink.href = pdfUrl;
    previewTitle.textContent = `Preview: ${filename}`;
    modal.style.display = 'block';
}

function closePreview() {
    modal.style.display = 'none';
    pdfPreview.src = '';
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
    
    fetch(`/preview/${pdfId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            document.getElementById('previewTitle').textContent = data.original_filename;
            document.getElementById('pdfPreview').src = `/pdf/${pdfId}#page=1`;
            document.getElementById('openPdfLink').href = `/pdf/${pdfId}`;
            
            // Update page navigation
            updatePageNavigation(data.page_count);
            
            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading preview:', error);
        });
}

function updatePageNavigation(totalPages) {
    const navHtml = `
        <div class="page-navigation">
            <button onclick="changePage(-1)" ${currentPage <= 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
            <span>Page ${currentPage} of ${totalPages}</span>
            <button onclick="changePage(1)" ${currentPage >= totalPages ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        </div>
    `;
    
    const existingNav = document.querySelector('.page-navigation');
    if (existingNav) {
        existingNav.remove();
    }
    
    document.querySelector('.preview-container').insertAdjacentHTML('beforebegin', navHtml);
}

function changePage(delta) {
    currentPage += delta;
    document.getElementById('pdfPreview').src = `/pdf/${currentPdfId}#page=${currentPage}`;
    updatePageNavigation(document.querySelector('.page-navigation span').textContent.split(' of ')[1]);
}