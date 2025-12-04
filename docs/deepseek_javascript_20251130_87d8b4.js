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