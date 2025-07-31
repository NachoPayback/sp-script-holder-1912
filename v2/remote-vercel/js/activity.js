// Activity Feed Module
// Handles activity log display and updates

// Activity state
let activityLog = [];

function addToActivityLog(username, action, status = 'pending', activityId = null) {
    const activityItems = document.getElementById('activityItems');
    const timestamp = new Date().toLocaleTimeString();
    
    const item = document.createElement('div');
    item.className = `activity-item ${status}`;
    item.setAttribute('data-user', username);
    item.setAttribute('data-action', action);
    if (activityId) {
        item.setAttribute('data-activity-id', activityId);
    }
    
    const statusIcon = status === 'success' ? '✅' : status === 'error' ? '❌' : '⏳';
    
    item.innerHTML = `
        <div class="activity-user">${username}</div>
        <div class="activity-action">${action}</div>
        <div class="activity-time">${timestamp} ${statusIcon}</div>
    `;
    
    activityItems.insertBefore(item, activityItems.firstChild);
    
    while (activityItems.children.length > 10) {
        activityItems.removeChild(activityItems.lastChild);
    }
}

function updateActivityLogResult(username, action, status) {
    const activityItems = document.getElementById('activityItems');
    const timestamp = new Date().toLocaleTimeString();
    
    // Find the most recent matching item
    const items = activityItems.querySelectorAll(`[data-user="${username}"][data-action="${action}"]`);
    if (items.length > 0) {
        const item = items[0]; // Most recent (first in list)
        item.className = `activity-item ${status}`;
        
        const statusIcon = status === 'success' ? '✅' : '❌';
        const timeEl = item.querySelector('.activity-time');
        if (timeEl) {
            timeEl.textContent = `${timestamp} ${statusIcon}`;
        }
    }
}

function updateActivityLogByCommandId(commandId, status) {
    const activityItems = document.getElementById('activityItems');
    const timestamp = new Date().toLocaleTimeString();
    
    const item = activityItems.querySelector(`[data-command-id="${commandId}"]`);
    if (item) {
        item.className = `activity-item ${status}`;
        
        const statusIcon = status === 'success' ? '✅' : '❌';
        const timeEl = item.querySelector('.activity-time');
        if (timeEl) {
            timeEl.textContent = `${timestamp} ${statusIcon}`;
        }
        
        const action = item.getAttribute('data-action');
        const message = status === 'success' ? 
            `✅ ${action} completed successfully` : 
            `❌ ${action} failed`;
        
        // Call UI module for toast
        window.UI.showToast(message);
    }
}

function clearActivityLog() {
    const activityItems = document.getElementById('activityItems');
    activityItems.innerHTML = '';
    activityLog = [];
}

// Public API
window.Activity = {
    addToActivityLog,
    updateActivityLogResult,
    updateActivityLogByCommandId,
    clearActivityLog
};