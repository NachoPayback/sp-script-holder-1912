let connectedHub = null;
let hubScripts = [];
let myAssignment = null;
let timerInterval = null;
let timerSeconds = 0;
let connectedUsers = [];
let activityLog = [];
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
    
    // Start the main application
    discoverHubs();
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
    connectedHub = null;
    myAssignment = null;
    showLoginInterface();
}

// Check authentication on load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
});

async function discoverHubs() {
    try {
        const response = await fetch('/api/hubs');
        const data = await response.json();
        
        const hubList = document.getElementById('hubList');
        hubList.innerHTML = '';
        
        if (!data.hubs || data.hubs.length === 0) {
            hubList.innerHTML = '<div class="loading">No active hubs found</div>';
            return;
        }
        
        data.hubs.forEach(hub => {
            const hubCard = document.createElement('div');
            hubCard.className = 'hub-card';
            hubCard.innerHTML = `
                <div class="hub-name">${hub.friendly_name}</div>
                <div class="hub-info">${hub.script_count} scripts • ${hub.mode} mode</div>
            `;
            
            hubCard.onclick = () => connectToHub(hub);
            hubList.appendChild(hubCard);
        });
    } catch (error) {
        console.error('Hub discovery error:', error);
    }
}

async function connectToHub(hub) {
    connectedHub = hub;
    myAssignment = null;
    
    document.getElementById('hubListContainer').style.display = 'none';
    document.getElementById('scriptsContainer').style.display = 'block';
    document.getElementById('sidebar').style.display = 'flex';
    document.getElementById('hubTitle').textContent = hub.friendly_name.toUpperCase();
    
    if (hub.mode === 'assigned') {
        await requestAssignment(hub.id);
    } else {
        await loadHubScripts(hub.id);
    }
    
    showScripts();
    updateConnectedUsers();
    showToast(`Connected to ${hub.friendly_name}`);
}

async function requestAssignment(hubId) {
    try {
        await fetch('/api/remote-assignment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hub_id: hubId, user_id: currentUser.username })
        });
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const response = await fetch(`/api/remote-assignment?hub_id=${hubId}&user_id=${currentUser.username}`);
        const data = await response.json();
        
        if (data.success && data.assignment) {
            myAssignment = data.assignment;
        }
    } catch (error) {
        console.error('Assignment request error:', error);
    }
}

async function loadHubScripts(hubId) {
    try {
        const response = await fetch(`/api/hub-scripts?hub_id=${hubId}`);
        const data = await response.json();
        
        if (data.success) {
            hubScripts = data.scripts;
        }
    } catch (error) {
        console.error('Load scripts error:', error);
        hubScripts = [];
    }
}

function showScripts() {
    const grid = document.getElementById('scriptGrid');
    grid.innerHTML = '';
    
    if (connectedHub.mode === 'assigned') {
        if (myAssignment && myAssignment.assigned_script) {
            const button = createScriptButton(
                myAssignment.assigned_script, 
                myAssignment.script_color || '#3b82f6',
                null, // Will use friendly name conversion
                connectedHub.show_script_names
            );
            grid.appendChild(button);
        } else {
            grid.innerHTML = '<div class="loading">Waiting for assignment...</div>';
        }
    } else {
        if (hubScripts.length === 0) {
            grid.innerHTML = '<div class="loading">No scripts available</div>';
            return;
        }
        
        hubScripts.forEach((script, index) => {
            const hue = (index * 137.5) % 360;
            const color = `hsl(${hue}, 70%, 50%)`;
            const scriptName = typeof script === 'string' ? script : script.script_name;
            const friendlyName = typeof script === 'string' ? script : script.friendly_name;
            const button = createScriptButton(scriptName, color, friendlyName, true); // Always show names in shared mode
            grid.appendChild(button);
        });
    }
}

function createScriptButton(scriptName, color, friendlyName = null, forceShowName = false) {
    const button = document.createElement('button');
    button.className = 'script-btn';
    button.style.borderColor = color;
    button.style.color = color;
    button.style.boxShadow = `0 0 20px ${color}33`;
    
    const executeText = document.createElement('div');
    executeText.className = 'execute-text';
    executeText.textContent = 'EXECUTE';
    button.appendChild(executeText);
    
    if (forceShowName || connectedHub.show_script_names) {
        const scriptNameEl = document.createElement('div');
        scriptNameEl.className = 'script-name';
        const displayName = friendlyName || scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        scriptNameEl.textContent = displayName.toUpperCase();
        button.appendChild(scriptNameEl);
    }
    
    button.onmouseover = () => {
        button.style.boxShadow = `0 0 40px ${color}66`;
    };
    button.onmouseout = () => {
        button.style.boxShadow = `0 0 20px ${color}33`;
    };
    
    button.onclick = () => executeScript(scriptName);
    
    return button;
}

async function executeScript(scriptName) {
    const resultDiv = document.getElementById('executionResult');
    resultDiv.style.display = 'block';
    resultDiv.className = 'result-display';
    resultDiv.innerHTML = `<strong>EXECUTING ${scriptName.toUpperCase()}...</strong>`;
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hub_id: connectedHub.id,
                script_name: scriptName,
                user_id: currentUser.username
            })
        });
        
        const result = await response.json();
        
        // Hide the result bubble and only use activity log
        resultDiv.style.display = 'none';
        
        if (result.success) {
            addToActivityLog(`${currentUser.username} executed: ${scriptName} ✅`, 'success');
            showToast(`✅ ${scriptName} executed successfully`);
        } else {
            addToActivityLog(`${currentUser.username} failed: ${scriptName} ❌ - ${result.error || 'Unknown error'}`, 'error');
            showToast(`❌ ${scriptName} failed`);
        }
    } catch (error) {
        console.error('Execution error:', error);
        resultDiv.style.display = 'none';
        addToActivityLog(`${currentUser.username} connection error: ${scriptName} - ${error.message}`, 'error');
        showToast(`❌ Connection error: ${scriptName}`);
    }
}

function backToHubs() {
    connectedHub = null;
    myAssignment = null;
    
    document.getElementById('hubListContainer').style.display = 'block';
    document.getElementById('scriptsContainer').style.display = 'none';
    document.getElementById('sidebar').style.display = 'none';
    
    discoverHubs();
}

function showSettings() {
    if (!connectedHub) return;
    
    const modal = document.getElementById('settingsModal');
    const modeRadios = modal.querySelectorAll('input[name="mode"]');
    const showNamesCheck = modal.querySelector('#showNames');
    
    modeRadios.forEach(radio => {
        radio.checked = radio.value === connectedHub.mode;
        radio.addEventListener('change', updateSettingsDisplay);
    });
    showNamesCheck.checked = connectedHub.show_script_names || false;
    
    updateSettingsDisplay();
    modal.style.display = 'flex';
}

function closeSettings() {
    document.getElementById('settingsModal').style.display = 'none';
}

function saveSettings() {
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const showNamesCheck = document.querySelector('#showNames');
    const enableTimerCheck = document.querySelector('#enableTimer');
    const timerMinutes = document.getElementById('timerMinutes').value;
    
    const selectedMode = [...modeRadios].find(r => r.checked)?.value;
    const showNames = showNamesCheck.checked;
    const enableTimer = enableTimerCheck.checked;
    
    if (selectedMode) {
        connectedHub.mode = selectedMode;
        connectedHub.show_script_names = showNames;
        
        showScripts();
        
        // Only start timer if explicitly enabled and in assigned mode
        if (selectedMode === 'assigned' && enableTimer && timerMinutes && parseInt(timerMinutes) > 0) {
            startTimer();
        } else {
            stopTimer(); // Stop timer if disabled or not in assigned mode
        }
        
        showToast(`Settings updated: ${selectedMode === 'assigned' ? '1 Button' : 'All Buttons'} mode`);
    }
    
    closeSettings();
}

function updateSettingsDisplay() {
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const selectedMode = [...modeRadios].find(r => r.checked)?.value || connectedHub?.mode || 'assigned';
    
    const showNamesSetting = document.getElementById('showNamesetting');
    const timerSetting = document.getElementById('timerSetting');
    const shuffleBtn = document.getElementById('shuffleBtn');
    const enableTimerCheck = document.querySelector('#enableTimer');
    const timerMinutesContainer = document.getElementById('timerMinutesContainer');
    
    if (selectedMode === 'shared') {
        showNamesSetting.style.display = 'none';
        timerSetting.style.display = 'none';
        shuffleBtn.style.display = 'none';
        if (timerInterval) {
            stopTimer();
        }
    } else {
        showNamesSetting.style.display = 'block';
        timerSetting.style.display = 'block';
        shuffleBtn.style.display = 'inline-block';
        
        // Show/hide timer minutes based on checkbox
        if (enableTimerCheck) {
            timerMinutesContainer.style.display = enableTimerCheck.checked ? 'block' : 'none';
        }
    }
}

// Add event listener for timer checkbox
document.addEventListener('DOMContentLoaded', function() {
    const enableTimerCheck = document.querySelector('#enableTimer');
    if (enableTimerCheck) {
        enableTimerCheck.addEventListener('change', updateSettingsDisplay);
    }
});

function shuffleScripts() {
    if (connectedHub.mode !== 'assigned') return;
    
    if (myAssignment) {
        requestAssignment(connectedHub.id);
        showToast('Button shuffled');
    }
}

function startTimer() {
    const minutes = parseInt(document.getElementById('timerMinutes').value) || 5;
    timerSeconds = minutes * 60;
    
    if (timerInterval) clearInterval(timerInterval);
    
    document.getElementById('timerSection').style.display = 'block';
    
    timerInterval = setInterval(() => {
        timerSeconds--;
        updateTimerDisplay();
        
        if (timerSeconds <= 0) {
            shuffleScripts();
            timerSeconds = minutes * 60;
            showToast('Timer completed - Scripts shuffled!');
        }
    }, 1000);
    
    updateTimerDisplay();
    showToast(`Timer started: ${minutes} minutes until shuffle`);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timerSeconds / 60);
    const seconds = timerSeconds % 60;
    const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    document.getElementById('timerDisplayValue').textContent = timeString;
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
        document.getElementById('timerSection').style.display = 'none';
        showToast('Timer stopped');
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

function addToActivityLog(message, type = 'info') {
    const activityItems = document.getElementById('activityItems');
    
    const timestamp = new Date().toLocaleTimeString();
    const item = document.createElement('div');
    item.className = `activity-item ${type}`;
    item.textContent = `${timestamp} - ${message}`;
    
    activityItems.insertBefore(item, activityItems.firstChild);
    
    while (activityItems.children.length > 10) {
        activityItems.removeChild(activityItems.lastChild);
    }
}

async function updateConnectedUsers() {
    if (!connectedHub || !currentUser) return;
    
    try {
        const response = await fetch(`/api/connected-users?hub_id=${connectedHub.id}`);
        const data = await response.json();
        
        if (data.success && data.users && data.users.length > 0) {
            connectedUsers = data.users;
        } else {
            connectedUsers = [currentUser.username];
        }
    } catch (error) {
        console.error('Error fetching connected users:', error);
        connectedUsers = [currentUser.username];
    }
    
    const usersContainer = document.getElementById('connectedUsers');
    if (usersContainer) {
        usersContainer.innerHTML = connectedUsers.map(user => 
            `<div class="user-item">${user}</div>`
        ).join('');
    }
}

// Auto-refresh
setInterval(() => {
    if (!connectedHub) {
        discoverHubs();
    } else {
        updateConnectedUsers();
    }
}, 30000);