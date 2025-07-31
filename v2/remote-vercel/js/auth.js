// Authentication Module
// Handles user login, logout, and authentication state

// Authentication state
let currentUser = null;
let authToken = null;

// Authentication functions
async function checkAuthentication() {
    const token = localStorage.getItem('sp_crew_token');
    
    if (token) {
        try {
            const response = await fetch('/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });
            
            const result = await response.json();
            
            if (result.valid) {
                authToken = token;
                currentUser = result.user;
                showMainInterface();
                return;
            }
        } catch (error) {
            console.error('Token verification failed:', error);
        }
    }
    
    showLoginInterface();
}

function showLoginInterface() {
    document.getElementById('loginContainer').style.display = 'flex';
    document.getElementById('mainContent').style.display = 'none';
    
    // Add login form handler
    document.getElementById('loginForm').onsubmit = async function(e) {
        e.preventDefault();
        await handleLogin();
    };
}

function showMainInterface() {
    document.getElementById('loginContainer').style.display = 'none';
    document.getElementById('mainContent').style.display = 'flex';
    document.getElementById('userDisplay').textContent = `Logged in as: ${currentUser.username}`;
    
    // Start the main application - call hub discovery
    window.Hub.discoverHubs();
}

async function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('loginError');
    
    try {
        const response = await fetch('/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            authToken = result.token;
            currentUser = result.user;
            localStorage.setItem('sp_crew_token', authToken);
            showMainInterface();
        } else {
            errorDiv.textContent = result.error || 'Login failed';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Connection error';
        errorDiv.style.display = 'block';
    }
}

function logout() {
    localStorage.removeItem('sp_crew_token');
    authToken = null;
    currentUser = null;
    
    // Reset hub state
    window.Hub.resetState();
    
    showLoginInterface();
}

// Public API - functions that other modules can access
window.Auth = {
    checkAuthentication,
    logout,
    getCurrentUser: () => currentUser,
    getAuthToken: () => authToken,
    isAuthenticated: () => !!currentUser
};