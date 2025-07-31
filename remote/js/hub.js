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
            // Better color distribution using golden ratio approach
            // This creates more distinct colors by spreading them more evenly
            const golden_ratio_conjugate = 0.618033988749895;
            const hue = (index * golden_ratio_conjugate * 360) % 360;
            
            // Vary saturation and lightness slightly for more visual variety
            const saturation = 65 + (index % 3) * 10; // 65%, 75%, 85%
            const lightness = 45 + (index % 2) * 10;  // 45%, 55%
            
            const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            const scriptName = typeof script === 'string' ? script : script.script_name;
            const friendlyName = typeof script === 'string' ? script : script.friendly_name;
            const button = createScriptButton(scriptName, color, friendlyName, true); // Always show names in shared mode
            grid.appendChild(button);
        });
    }
}

function createScriptButton(scriptName, color, friendlyName = null, forceShowName = false) {
    console.log(`[DEBUG] Creating button for: ${scriptName}`);
    
    // Create SVG button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'script-btn-container';
    buttonContainer.style.position = 'relative';
    buttonContainer.style.width = '180px';
    buttonContainer.style.height = '180px';
    buttonContainer.style.cursor = 'pointer';
    buttonContainer.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    
    // Create SVG hexagon
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '180');
    svg.setAttribute('height', '180');
    svg.setAttribute('viewBox', '0 0 752.44 682.42');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M245.57,681.92c-40.75,0-78.72-21.92-99.1-57.21L15.83,398.42c-20.37-35.29-20.37-79.14,0-114.43L146.48,57.71C166.85,22.42,204.82.5,245.57.5h261.29c40.75,0,78.72,21.92,99.1,57.21l130.65,226.29c20.37,35.29,20.37,79.14,0,114.43l-130.65,226.29c-20.38,35.29-58.35,57.21-99.1,57.21H245.57Z');
    path.setAttribute('fill', 'rgba(0, 0, 0, 0.3)');
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', '6');
    path.style.filter = `drop-shadow(0 0 20px ${color}33)`;
    
    // Add gradient
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'radialGradient');
    gradient.setAttribute('id', `grad-${scriptName}`);
    gradient.setAttribute('cx', '30%');
    gradient.setAttribute('cy', '30%');
    
    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('stop-color', 'rgba(255, 255, 255, 0.1)');
    
    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '50%');
    stop2.setAttribute('stop-color', 'transparent');
    
    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.appendChild(defs);
    
    path.setAttribute('fill', `url(#grad-${scriptName})`);
    svg.appendChild(path);
    buttonContainer.appendChild(svg);
    
    // Create text content
    const textContainer = document.createElement('div');
    textContainer.className = 'script-btn-text';
    textContainer.style.position = 'absolute';
    textContainer.style.top = '50%';
    textContainer.style.left = '50%';
    textContainer.style.transform = 'translate(-50%, -50%)';
    textContainer.style.textAlign = 'center';
    textContainer.style.color = color;
    textContainer.style.pointerEvents = 'none';
    textContainer.style.zIndex = '10';
    
    const executeText = document.createElement('div');
    executeText.className = 'execute-text';
    executeText.textContent = 'EXECUTE';
    executeText.style.fontSize = '1.1rem';
    executeText.style.fontWeight = '700';
    executeText.style.textTransform = 'uppercase';
    executeText.style.letterSpacing = '0.05em';
    textContainer.appendChild(executeText);
    
    if (forceShowName || connectedHub.show_script_names) {
        const scriptNameEl = document.createElement('div');
        scriptNameEl.className = 'script-name';
        const displayName = friendlyName || scriptFriendlyNames[scriptName]?.friendly_name || scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        scriptNameEl.textContent = displayName.toUpperCase();
        scriptNameEl.style.fontSize = '0.75rem';
        scriptNameEl.style.fontWeight = '600';
        scriptNameEl.style.marginTop = '8px';
        scriptNameEl.style.opacity = '0.9';
        scriptNameEl.style.maxWidth = '140px';
        scriptNameEl.style.lineHeight = '1.2';
        textContainer.appendChild(scriptNameEl);
    }
    
    buttonContainer.appendChild(textContainer);
    
    // Hover effects
    buttonContainer.onmouseover = () => {
        buttonContainer.style.transform = 'scale(1.08)';
        path.style.filter = `drop-shadow(0 0 40px ${color}66)`;
    };
    buttonContainer.onmouseout = () => {
        buttonContainer.style.transform = 'scale(1)';
        path.style.filter = `drop-shadow(0 0 20px ${color}33)`;
    };
    
    buttonContainer.onclick = () => executeScript(scriptName);
    
    return buttonContainer;
}

async function executeScript(scriptName) {
    console.log(`[DEBUG] executeScript called for: ${scriptName}`);
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
                }
            }, 15000); // 15 second fallback timeout
        } else {
            window.Activity.updateActivityLogResult(currentUser.username, displayName, 'error');
        }
    } catch (error) {
        console.error('Execution error:', error);
        window.Activity.updateActivityLogResult(currentUser.username, displayName, 'error');
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