// Loading overlay functionality
document.addEventListener('DOMContentLoaded', function() {
    // Create the loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loading-overlay';
    loadingOverlay.className = 'fixed inset-0 flex items-center justify-center z-50 bg-forge-dark bg-opacity-70 backdrop-blur-md';
    loadingOverlay.style.display = 'none';
    
    // Create spinner container
    const spinnerContainer = document.createElement('div');
    spinnerContainer.className = 'glass-panel p-8 rounded-xl flex flex-col items-center';
    
    // Create spinner
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    
    // Create loading text
    const loadingText = document.createElement('p');
    loadingText.className = 'text-white mt-4 text-lg';
    loadingText.textContent = 'Procesando...';
    
    // Assemble elements
    spinnerContainer.appendChild(spinner);
    spinnerContainer.appendChild(loadingText);
    loadingOverlay.appendChild(spinnerContainer);
    
    // Add to body
    document.body.appendChild(loadingOverlay);
    
    // Find all forms that should trigger the loading overlay
    const forms = document.querySelectorAll('form[data-loading="true"]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Show the loading overlay
            showLoading();
        });
    });
    
    // Find buttons that should trigger the loading overlay
    const loadingButtons = document.querySelectorAll('[data-loading="true"]');
    
    loadingButtons.forEach(button => {
        // Skip if it's a form, already handled above
        if (button.tagName === 'FORM') return;
        
        button.addEventListener('click', function(e) {
            // If button is in a form, let the form handler take care of it
            if (button.form) return;
            
            // Check if button has an href or onclick
            if (button.getAttribute('href') || button.getAttribute('onclick')) {
                showLoading();
            }
        });
    });
});

// Function to show the loading overlay
function showLoading(customMessage) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        // Update message if provided
        if (customMessage) {
            const textElem = overlay.querySelector('p');
            if (textElem) textElem.textContent = customMessage;
        }
        
        overlay.style.display = 'flex';
    }
}

// Function to hide the loading overlay
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}
