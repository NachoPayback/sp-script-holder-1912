// UI Module
// Handles settings, timers, toasts, and user interface updates

// UI state
let timerInterval = null;
let timerSeconds = 0;
let connectedUsers = [];

function showSettings() {
    const connectedHub = window.Hub.getConnectedHub();
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
        const connectedHub = window.Hub.getConnectedHub();
        if (connectedHub) {
            connectedHub.mode = selectedMode;
            connectedHub.show_script_names = showNames;
            
            // Update hub scripts display
            window.Hub.showScripts();
            
            // Only start timer if explicitly enabled and in assigned mode
            if (selectedMode === 'assigned' && enableTimer && timerMinutes && parseInt(timerMinutes) > 0) {
                startTimer();
            } else {
                stopTimer(); // Stop timer if disabled or not in assigned mode
            }
            
            showToast(`Settings updated: ${selectedMode === 'assigned' ? '1 Button' : 'All Buttons'} mode`);
        }
    }
    
    closeSettings();
}

function updateSettingsDisplay() {
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    const connectedHub = window.Hub.getConnectedHub();
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

function shuffleScripts() {
    const connectedHub = window.Hub.getConnectedHub();
    const myAssignment = window.Hub.getMyAssignment();
    
    if (connectedHub?.mode !== 'assigned') return;
    
    if (myAssignment) {
        window.Hub.requestAssignment(connectedHub.id);
        showToast('Button shuffled');
    }
}

function startTimer() {
    const minutes = parseInt(document.getElementById('timerMinutes').value) || 5;
    timerSeconds = minutes * 60;
    
    if (timerInterval) clearInterval(timerInterval);
    
    document.getElementById('timerSection').style.display = 'block';
    updateTimerDisplay();
    
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
    const timerSection = document.getElementById('timerSection');
    const sidebar = document.getElementById('sidebar');
    
    if (timerSection && sidebar) {
        const isTimerVisible = timerSection.style.display !== 'none';
        if (isTimerVisible) {
            sidebar.classList.add('timer-active');
        } else {
            sidebar.classList.remove('timer-active');
        }
    }
    
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
        updateTimerDisplay();
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

async function updateConnectedUsers() {
    const connectedHub = window.Hub.getConnectedHub();
    const currentUser = window.Auth.getCurrentUser();
    
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

// Add event listener for timer checkbox when DOM is ready
function initializeUIEventListeners() {
    const enableTimerCheck = document.querySelector('#enableTimer');
    if (enableTimerCheck) {
        enableTimerCheck.addEventListener('change', updateSettingsDisplay);
    }
}

// Public API
window.UI = {
    showSettings,
    closeSettings,
    saveSettings,
    updateSettingsDisplay,
    shuffleScripts,
    startTimer,
    stopTimer,
    showToast,
    updateConnectedUsers,
    initializeUIEventListeners
};