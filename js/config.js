// config.js - API Configuration for Production/Development
const API_CONFIG = {
    // Auto-detect environment
    isDevelopment: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    
    // API Base URLs
    getBaseURL() {
        if (this.isDevelopment) {
            return 'http://localhost:8000';
        } else {
            // Production: REPLACE THIS with your actual Render backend URL
            // Example: return 'https://inboxqualify-api.onrender.com';
            return 'https://inboxqualify-api.onrender.com';
        }
    },
    
    // Helper function to build API URLs
    getURL(endpoint) {
        const base = this.getBaseURL();
        // Remove leading slash from endpoint if present
        const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
        return `${base}/${cleanEndpoint}`;
    }
};

// Make it globally available
window.API_CONFIG = API_CONFIG;

// Debug: Log the current configuration
console.log('🔧 API Configuration:', {
    isDevelopment: API_CONFIG.isDevelopment,
    baseURL: API_CONFIG.getBaseURL(),
    hostname: window.location.hostname
});
