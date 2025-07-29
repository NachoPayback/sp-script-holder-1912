/**
 * SP Crew Control V2 - Session Manager
 * Manages session state, hub registry, and remote coordination
 */

class SessionManager {
  constructor() {
    // In-memory storage (Vercel functions are stateless, but this works for active sessions)
    this.hubs = new Map(); // hub_id -> hub_info
    this.sessions = new Map(); // session_id -> session_data
    this.remotes = new Map(); // remote_id -> remote_info
  }

  // =========================================================================
  // HUB MANAGEMENT
  // =========================================================================

  registerHub(hubData) {
    const hubId = hubData.hub_id;
    const hubInfo = {
      ...hubData,
      registered_at: new Date().toISOString(),
      last_heartbeat: new Date().toISOString(),
      status: 'online'
    };
    
    this.hubs.set(hubId, hubInfo);
    console.log(`Hub registered: ${hubId} (${hubData.hub_name})`);
    return { success: true, hub_id: hubId };
  }

  getAvailableHubs() {
    const now = Date.now();
    const activeHubs = [];
    
    for (const [hubId, hubInfo] of this.hubs.entries()) {
      const lastHeartbeat = new Date(hubInfo.last_heartbeat).getTime();
      const timeSinceHeartbeat = now - lastHeartbeat;
      
      // Consider hub offline if no heartbeat for 2 minutes
      if (timeSinceHeartbeat < 120000) {
        // Count connected remotes for this hub
        const connectedRemotes = Array.from(this.remotes.values())
          .filter(r => r.current_hub === hubId).length;
          
        activeHubs.push({
          hub_id: hubId,
          hub_name: hubInfo.hub_name,
          hub_location: hubInfo.hub_location || 'Unknown Location',
          script_count: hubInfo.scripts ? hubInfo.scripts.length : 0,
          connected_remotes: connectedRemotes,
          max_remotes: hubInfo.max_remotes || 6,
          latency_ms: this.calculateLatency(hubInfo.websocket_url)
        });
      } else {
        // Mark hub as offline
        hubInfo.status = 'offline';
      }
    }
    
    return activeHubs.sort((a, b) => a.latency_ms - b.latency_ms);
  }

  updateHubHeartbeat(hubId) {
    const hubInfo = this.hubs.get(hubId);
    if (hubInfo) {
      hubInfo.last_heartbeat = new Date().toISOString();
      hubInfo.status = 'online';
      return true;
    }
    return false;
  }

  // =========================================================================
  // SESSION MANAGEMENT  
  // =========================================================================

  createSession(remoteId, hubId, requestedMode = 'single_button') {
    const sessionId = `session_${hubId}_${Date.now()}`;
    const hubInfo = this.hubs.get(hubId);
    
    if (!hubInfo) {
      return { success: false, message: 'Hub not found' };
    }

    // Check hub capacity
    const existingRemotes = Array.from(this.remotes.values())
      .filter(r => r.current_hub === hubId);
    
    if (existingRemotes.length >= hubInfo.max_remotes) {
      return { success: false, message: 'Hub at capacity' };
    }

    // Create or join existing session for this hub
    let session = Array.from(this.sessions.values())
      .find(s => s.hub_id === hubId && s.status === 'active');
    
    if (!session) {
      session = {
        session_id: sessionId,
        hub_id: hubId,
        hub_info: hubInfo,
        current_mode: 'single_button', // Always start in single button mode
        connected_remotes: [],
        script_assignments: {},
        created_at: new Date().toISOString(),
        status: 'active',
        activity_log: []
      };
      this.sessions.set(sessionId, session);
    }

    // Add remote to session
    session.connected_remotes.push(remoteId);
    
    // Update remote info
    this.remotes.set(remoteId, {
      remote_id: remoteId,
      current_session: session.session_id,
      current_hub: hubId,
      joined_at: new Date().toISOString(),
      status: 'connected'
    });

    // Assign script if in single button mode
    let assignedScript = null;
    if (session.current_mode === 'single_button') {
      assignedScript = this.assignScriptToRemote(session, remoteId);
    }

    return {
      success: true,
      session_id: session.session_id,
      current_mode: session.current_mode,
      assigned_script: assignedScript,
      available_scripts: hubInfo.scripts || [],
      websocket_url: hubInfo.websocket_url
    };
  }

  // =========================================================================
  // MODE MANAGEMENT
  // =========================================================================

  requestModeChange(sessionId, remoteId, newMode) {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return { success: false, message: 'Session not found' };
    }

    if (!session.connected_remotes.includes(remoteId)) {
      return { success: false, message: 'Remote not in session' };
    }

    // Generate transition ID for coordinating UI updates
    const transitionId = `transition_${Date.now()}`;
    
    // Log mode change activity
    this.logActivity(sessionId, {
      remote_id: remoteId,
      action: 'mode_change_requested',
      details: `${session.current_mode} → ${newMode}`,
      success: true
    });

    return {
      success: true,
      transition_id: transitionId,
      old_mode: session.current_mode,
      new_mode: newMode,
      affected_remotes: session.connected_remotes
    };
  }

  completeModeTransition(sessionId, transitionId, newMode) {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return { success: false, message: 'Session not found' };
    }

    // Update session mode
    session.current_mode = newMode;

    // Handle assignments based on new mode
    let newAssignments = {};
    if (newMode === 'single_button') {
      // Reassign scripts to remotes
      for (const remoteId of session.connected_remotes) {
        newAssignments[remoteId] = this.assignScriptToRemote(session, remoteId);
      }
      session.script_assignments = newAssignments;
    } else {
      // All buttons mode - clear assignments
      session.script_assignments = {};
    }

    this.logActivity(sessionId, {
      remote_id: 'system',
      action: 'mode_changed',
      details: `Session switched to ${newMode}`,
      success: true
    });

    return {
      success: true,
      session_id: sessionId,
      new_mode: newMode,
      new_assignments: newAssignments
    };
  }

  // =========================================================================
  // SCRIPT ASSIGNMENT (Single Button Mode)
  // =========================================================================

  assignScriptToRemote(session, remoteId) {
    const availableScripts = session.hub_info.scripts || [];
    if (availableScripts.length === 0) return null;

    // Get currently assigned scripts
    const assignedScripts = Object.values(session.script_assignments);
    
    // Find unassigned scripts
    const unassignedScripts = availableScripts.filter(script => 
      !assignedScripts.includes(script.name)
    );

    // If no unassigned scripts, use any available script
    const scriptPool = unassignedScripts.length > 0 ? unassignedScripts : availableScripts;
    
    // Randomly assign a script
    const randomScript = scriptPool[Math.floor(Math.random() * scriptPool.length)];
    session.script_assignments[remoteId] = randomScript.name;
    
    return randomScript.name;
  }

  shuffleScriptAssignments(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session || session.current_mode !== 'single_button') {
      return { success: false, message: 'Cannot shuffle in current mode' };
    }

    const availableScripts = session.hub_info.scripts || [];
    const remoteIds = session.connected_remotes;
    
    if (availableScripts.length < remoteIds.length) {
      return { success: false, message: 'Not enough scripts for all remotes' };
    }

    // Shuffle script assignments
    const shuffledScripts = [...availableScripts]
      .sort(() => Math.random() - 0.5)
      .slice(0, remoteIds.length);

    const newAssignments = {};
    remoteIds.forEach((remoteId, index) => {
      newAssignments[remoteId] = shuffledScripts[index].name;
    });

    session.script_assignments = newAssignments;

    this.logActivity(sessionId, {
      remote_id: 'system',
      action: 'scripts_shuffled',
      details: `Reassigned ${remoteIds.length} remotes`,
      success: true
    });

    return { success: true, new_assignments: newAssignments };
  }

  // =========================================================================
  // ACTIVITY LOGGING
  // =========================================================================

  logActivity(sessionId, activity) {
    const session = this.sessions.get(sessionId);
    if (!session) return false;

    const logEntry = {
      timestamp: new Date().toISOString(),
      ...activity
    };

    session.activity_log.push(logEntry);
    
    // Keep only last 100 activities to prevent memory bloat
    if (session.activity_log.length > 100) {
      session.activity_log = session.activity_log.slice(-100);
    }

    return logEntry;
  }

  getRecentActivity(sessionId, limit = 20) {
    const session = this.sessions.get(sessionId);
    if (!session) return [];

    return session.activity_log
      .slice(-limit)
      .reverse(); // Most recent first
  }

  // =========================================================================
  // UTILITY METHODS
  // =========================================================================

  calculateLatency(websocketUrl) {
    // Simple latency estimation (in real implementation, could ping the URL)
    // For now, return random latency between 20-100ms
    return Math.floor(Math.random() * 80) + 20;
  }

  getSessionStatus(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return null;

    const remoteDetails = session.connected_remotes.map(remoteId => {
      const remote = this.remotes.get(remoteId);
      return {
        remote_id: remoteId,
        assigned_script: session.script_assignments[remoteId] || null,
        status: remote ? remote.status : 'unknown'
      };
    });

    return {
      session_id: sessionId,
      current_mode: session.current_mode,
      connected_remotes: remoteDetails,
      hub_info: {
        hub_id: session.hub_id,
        hub_name: session.hub_info.hub_name,
        script_count: session.hub_info.scripts?.length || 0
      },
      recent_activity: this.getRecentActivity(sessionId, 10)
    };
  }

  cleanupInactiveSessions() {
    const now = Date.now();
    const sessionsToRemove = [];

    for (const [sessionId, session] of this.sessions.entries()) {
      const createdAt = new Date(session.created_at).getTime();
      const sessionAge = now - createdAt;
      
      // Remove sessions older than 24 hours with no activity
      if (sessionAge > 24 * 60 * 60 * 1000 && session.connected_remotes.length === 0) {
        sessionsToRemove.push(sessionId);
      }
    }

    sessionsToRemove.forEach(sessionId => {
      this.sessions.delete(sessionId);
      console.log(`Cleaned up inactive session: ${sessionId}`);
    });

    return sessionsToRemove.length;
  }
}

// Export singleton instance
const sessionManager = new SessionManager();
module.exports = sessionManager;