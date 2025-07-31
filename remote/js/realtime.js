// Real-time Module
// Handles Supabase real-time subscriptions and WebSocket communications

// Real-time state
let realtimeChannel = null;

function setupRealtimeSubscriptions() {
    if (realtimeChannel) {
        realtimeChannel.unsubscribe();
    }
    
    const connectedHub = window.Hub.getConnectedHub();
    if (!connectedHub) return;
    
    // Subscribe to script results for this hub
    realtimeChannel = window.supabaseClient
        .channel(`hub-results-${connectedHub.id}`)
        .on('postgres_changes', {
            event: 'INSERT',
            schema: 'public',
            table: 'script_results'
        }, (payload) => {
            console.log('Real-time result received:', payload);
            handleScriptResult(payload.new);
        })
        .subscribe();
    
    console.log(`Real-time subscriptions setup for hub: ${connectedHub.id}`);
}

function handleScriptResult(result) {
    if (!result || !result.command_id) return;
    
    console.log('Handling script result for command:', result.command_id);
    
    // Find the matching activity item by command ID
    const status = result.success ? 'success' : 'error';
    
    // Call activity module function
    window.Activity.updateActivityLogByCommandId(result.command_id, status);
}

function cleanupRealtimeSubscriptions() {
    if (realtimeChannel) {
        realtimeChannel.unsubscribe();
        realtimeChannel = null;
    }
}

// Public API
window.Realtime = {
    setupRealtimeSubscriptions,
    cleanupRealtimeSubscriptions
};