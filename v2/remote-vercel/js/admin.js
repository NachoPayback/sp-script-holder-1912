// Admin Module
// Handles admin functions like managing script friendly names

async function showScriptNames() {
    const modal = document.getElementById('scriptNamesModal');
    modal.style.display = 'flex';
    
    await loadAndDisplayScriptNames();
}

function closeScriptNames() {
    document.getElementById('scriptNamesModal').style.display = 'none';
}

async function refreshScriptNames() {
    await loadAndDisplayScriptNames();
    window.UI.showToast('Script names refreshed');
}

async function loadAndDisplayScriptNames() {
    try {
        // Get all available scripts from current hub
        const connectedHub = window.Hub.getConnectedHub();
        const hubScripts = window.Hub.getHubScripts();
        const myAssignment = window.Hub.getMyAssignment();
        
        if (!connectedHub) {
            document.getElementById('scriptNamesList').innerHTML = '<p>No hub connected</p>';
            return;
        }
        
        // Collect all script names
        const scriptNames = new Set();
        hubScripts.forEach(script => {
            const scriptName = typeof script === 'string' ? script : script.script_name;
            scriptNames.add(scriptName);
        });
        if (myAssignment?.assigned_script) {
            scriptNames.add(myAssignment.assigned_script);
        }
        
        // Load current friendly names from database
        const response = await fetch('/api/script-friendly-names');
        const data = await response.json();
        const friendlyNames = data.success ? data.friendly_names : {};
        
        // Render the list
        const listContainer = document.getElementById('scriptNamesList');
        listContainer.innerHTML = '';
        
        if (scriptNames.size === 0) {
            listContainer.innerHTML = '<p>No scripts found</p>';
            return;
        }
        
        Array.from(scriptNames).sort().forEach(scriptName => {
            const item = document.createElement('div');
            item.className = 'script-name-item';
            item.style.cssText = `
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px;
                margin: 5px 0;
                background: rgba(30, 41, 59, 0.3);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 6px;
            `;
            
            const currentFriendlyName = friendlyNames[scriptName]?.friendly_name || '';
            const autoName = scriptName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            item.innerHTML = `
                <div style="flex: 1; min-width: 0;">
                    <strong style="color: #3b82f6;">${scriptName}</strong>
                    <div style="font-size: 12px; color: #94a3b8;">Auto: ${autoName}</div>
                </div>
                <input type="text" 
                       value="${currentFriendlyName}" 
                       placeholder="Custom friendly name..."
                       data-script-name="${scriptName}"
                       style="flex: 1; padding: 8px; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); color: #e2e8f0; border-radius: 4px;">
                <button onclick="window.Admin.saveScriptName('${scriptName}')" 
                        style="padding: 8px 12px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;">SAVE</button>
                ${currentFriendlyName ? `<button onclick="window.Admin.deleteScriptName('${scriptName}')" 
                        style="padding: 8px 12px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">DELETE</button>` : ''}
            `;
            
            listContainer.appendChild(item);
        });
        
    } catch (error) {
        console.error('Failed to load script names:', error);
        document.getElementById('scriptNamesList').innerHTML = '<p>Error loading script names</p>';
    }
}

async function saveScriptName(scriptName) {
    try {
        const input = document.querySelector(`input[data-script-name="${scriptName}"]`);
        const friendlyName = input.value.trim();
        
        if (!friendlyName) {
            window.UI.showToast('Please enter a friendly name');
            return;
        }
        
        const response = await fetch('/api/script-friendly-names', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script_name: scriptName,
                friendly_name: friendlyName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.UI.showToast(`✅ Saved: ${friendlyName}`);
            await loadAndDisplayScriptNames(); // Refresh the list
            
            // Reload friendly names in hub module
            await window.Hub.reloadFriendlyNames();
        } else {
            window.UI.showToast(`❌ Failed to save: ${data.error}`);
        }
        
    } catch (error) {
        console.error('Failed to save script name:', error);
        window.UI.showToast('❌ Error saving script name');
    }
}

async function deleteScriptName(scriptName) {
    try {
        const response = await fetch('/api/script-friendly-names', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script_name: scriptName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            window.UI.showToast(`🗑️ Deleted friendly name for ${scriptName}`);
            await loadAndDisplayScriptNames(); // Refresh the list
            
            // Reload friendly names in hub module
            await window.Hub.reloadFriendlyNames();
        } else {
            window.UI.showToast(`❌ Failed to delete: ${data.error}`);
        }
        
    } catch (error) {
        console.error('Failed to delete script name:', error);
        window.UI.showToast('❌ Error deleting script name');
    }
}

// Public API
window.Admin = {
    showScriptNames,
    closeScriptNames,
    refreshScriptNames,
    saveScriptName,
    deleteScriptName
};