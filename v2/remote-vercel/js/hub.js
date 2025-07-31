// Hub Module
// Handles hub discovery, connection, script management, and execution

// Hub state
let connectedHub = null;
let hubScripts = [];
let myAssignment = null;
let scriptFriendlyNames = {}; // Will be loaded from database

async function loadScriptFriendlyNames(scriptNames = null) {
    try {
        let url = '/api/script-friendly-names';
        if (scriptNames && scriptNames.length > 0) {
            url += `?script_names=${scriptNames.join(',')}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            scriptFriendlyNames = data.friendly_names;
            console.log('Loaded friendly names:', Object.keys(scriptFriendlyNames).length);
        }
    } catch (error) {
        console.error('Failed to load script friendly names:', error);
        // Keep existing names if load fails
    }
}

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
    
    // Set up real-time subscriptions for this hub
    window.Realtime.setupRealtimeSubscriptions();
    
    if (hub.mode === 'assigned') {
        await requestAssignment(hub.id);
    } else {
        await loadHubScripts(hub.id);
    }
    
    // Load friendly names for the scripts we have
    const scriptNames = hubScripts.map(script => 
        typeof script === 'string' ? script : script.script_name
    );
    if (myAssignment?.assigned_script) {
        scriptNames.push(myAssignment.assigned_script);
    }
    await loadScriptFriendlyNames(scriptNames);
    
    showScripts();
    
    // Update connected users and show toast
    window.UI.updateConnectedUsers();
    window.UI.showToast(`Connected to ${hub.friendly_name}`);
}

async function requestAssignment(hubId) {
    const currentUser = window.Auth.getCurrentUser();
    if (!currentUser) return;
    
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
        const displayName = friendlyName || scriptFriendlyNames[scriptName]?.friendly_name || scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
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
    const currentUser = window.Auth.getCurrentUser();
    if (!currentUser) return;
    
    // Don't show executing bar - just add to activity log immediately
    // In "All Buttons" mode (shared), always show script names
    // In "1 Button" mode (assigned), show "Button Pressed" when names are hidden
    const displayName = (connectedHub.mode === 'shared' || connectedHub.show_script_names) ? 
        (scriptFriendlyNames[scriptName]?.friendly_name || scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())) : 
        'Button Pressed';
    
    const activityId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Add to activity log
    window.Activity.addToActivityLog(currentUser.username, displayName, 'pending', activityId);
    
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
        
        if (result.success && result.commandId) {
            // Command sent successfully - store command ID for real-time matching
            console.log(`Command sent: ${result.commandId}`);
            
            // Store command ID in the activity item
            const activityItems = document.getElementById('activityItems');
            const item = activityItems.querySelector(`[data-activity-id="${activityId}"]`);
            if (item) {
                item.setAttribute('data-command-id', result.commandId);
            }
            
            // Set a timeout fallback in case real-time fails
            setTimeout(() => {
                // Check if this command is still pending
                const item = activityItems.querySelector(`[data-command-id="${result.commandId}"]`);
                if (item && item.className.includes('pending')) {
                    window.Activity.updateActivityLogByCommandId(result.commandId, 'error');
                    window.UI.showToast(`⏱️ ${displayName} timed out`);
                }
            }, 15000); // 15 second fallback timeout
        } else {
            window.Activity.updateActivityLogResult(currentUser.username, displayName, 'error');
            window.UI.showToast(`❌ ${displayName} failed to send`);
        }
    } catch (error) {
        console.error('Execution error:', error);
        window.Activity.updateActivityLogResult(currentUser.username, displayName, 'error');
        window.UI.showToast(`❌ Connection error: ${displayName}`);
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

function resetState() {
    connectedHub = null;
    myAssignment = null;
    hubScripts = [];
    scriptFriendlyNames = {};
}

async function reloadFriendlyNames() {
    // Reload friendly names for current scripts
    const scriptNames = hubScripts.map(script => 
        typeof script === 'string' ? script : script.script_name
    );
    if (myAssignment?.assigned_script) {
        scriptNames.push(myAssignment.assigned_script);
    }
    await loadScriptFriendlyNames(scriptNames);
    
    // Refresh the display
    showScripts();
}

// Public API
window.Hub = {
    discoverHubs,
    connectToHub,
    requestAssignment,
    loadHubScripts,
    showScripts,
    executeScript,
    backToHubs,
    resetState,
    reloadFriendlyNames,
    getConnectedHub: () => connectedHub,
    getHubScripts: () => hubScripts,
    getMyAssignment: () => myAssignment
};