// Main Application Coordinator
// Initializes Supabase client and coordinates module interactions

// Initialize Supabase client for real-time subscriptions
const { createClient } = supabase;
const supabaseClient = createClient(
    'https://qcefzjjxnwccjivsbtgb.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

// Make Supabase client globally available
window.supabaseClient = supabaseClient;

// Initialize UI event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI event listeners
    window.UI.initializeUIEventListeners();
    
    // Check authentication on load
    window.Auth.checkAuthentication();
});

// Auto-refresh functionality
setInterval(() => {
    const connectedHub = window.Hub.getConnectedHub();
    if (!connectedHub) {
        // If no hub connected, discover hubs
        window.Hub.discoverHubs();
    } else {
        // If hub connected, update connected users
        window.UI.updateConnectedUsers();
    }
}, 30000);