/**
 * SP Crew Control V2 - Session Management API
 * Handles session joining, mode changes, and session status
 */

const sessionManager = require('../lib/session-manager');

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).json({ message: 'OK' });
  }

  try {
    switch (req.method) {
      case 'POST':
        return await handleSessionJoin(req, res);
      case 'PUT':
        return await handleModeChange(req, res);
      case 'GET':
        return await handleSessionStatus(req, res);
      default:
        return res.status(405).json({ 
          success: false, 
          message: 'Method not allowed' 
        });
    }
  } catch (error) {
    console.error('Session management error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}

/**
 * Handle session join requests
 * POST /api/join-session
 */
async function handleSessionJoin(req, res) {
  const { remote_id, remote_name, hub_id, requested_mode } = req.body;

  // Validate required fields
  if (!remote_id || !hub_id) {
    return res.status(400).json({
      success: false,
      message: 'remote_id and hub_id are required'
    });
  }

  // Validate remote_id format
  if (!/^[a-zA-Z0-9_-]+$/.test(remote_id)) {
    return res.status(400).json({
      success: false,
      message: 'Invalid remote_id format. Use only alphanumeric characters, underscores, and hyphens.'
    });
  }

  // Validate mode if specified
  const validModes = ['single_button', 'all_buttons'];
  if (requested_mode && !validModes.includes(requested_mode)) {
    return res.status(400).json({
      success: false,
      message: `Invalid mode. Must be one of: ${validModes.join(', ')}`
    });
  }

  // Create or join session
  const result = sessionManager.createSession(
    remote_id, 
    hub_id, 
    requested_mode || 'single_button'
  );

  if (result.success) {
    return res.status(200).json({
      type: 'session_join_response',
      success: true,
      session_id: result.session_id,
      current_mode: result.current_mode,
      assigned_script: result.assigned_script,
      available_scripts: result.available_scripts,
      websocket_url: result.websocket_url,
      message: 'Successfully joined session'
    });
  } else {
    return res.status(400).json({
      type: 'session_join_response',
      success: false,
      message: result.message
    });
  }
}

/**
 * Handle mode change requests
 * PUT /api/join-session
 */
async function handleModeChange(req, res) {
  const { session_id, remote_id, new_mode, action } = req.body;

  // Validate required fields
  if (!session_id || !remote_id || !new_mode) {
    return res.status(400).json({
      success: false,
      message: 'session_id, remote_id, and new_mode are required'
    });
  }

  // Validate mode
  const validModes = ['single_button', 'all_buttons'];
  if (!validModes.includes(new_mode)) {
    return res.status(400).json({
      success: false,
      message: `Invalid mode. Must be one of: ${validModes.join(', ')}`
    });
  }

  if (action === 'request_mode_change') {
    // Initial mode change request
    const result = sessionManager.requestModeChange(session_id, remote_id, new_mode);
    
    if (result.success) {
      return res.status(200).json({
        type: 'mode_change_broadcast',
        success: true,
        session_id: session_id,
        new_mode: new_mode,
        transition_id: result.transition_id,
        initiated_by: remote_id,
        affected_remotes: result.affected_remotes,
        message: 'Mode change initiated'
      });
    } else {
      return res.status(400).json({
        success: false,
        message: result.message
      });
    }
  } else if (action === 'complete_mode_change') {
    // Complete mode transition
    const { transition_id } = req.body;
    
    if (!transition_id) {
      return res.status(400).json({
        success: false,
        message: 'transition_id is required for completing mode change'
      });
    }

    const result = sessionManager.completeModeTransition(session_id, transition_id, new_mode);
    
    if (result.success) {
      return res.status(200).json({
        type: 'mode_transition_complete',
        success: true,
        session_id: result.session_id,
        new_mode: result.new_mode,
        new_assignments: result.new_assignments,
        transition_id: transition_id,
        message: 'Mode transition completed'
      });
    } else {
      return res.status(400).json({
        success: false,
        message: result.message
      });
    }
  } else {
    return res.status(400).json({
      success: false,
      message: 'Invalid action. Must be "request_mode_change" or "complete_mode_change"'
    });
  }
}

/**
 * Handle session status requests
 * GET /api/join-session?session_id=xxx
 */
async function handleSessionStatus(req, res) {
  const { session_id } = req.query;

  if (!session_id) {
    return res.status(400).json({
      success: false,
      message: 'session_id parameter is required'
    });
  }

  const status = sessionManager.getSessionStatus(session_id);

  if (status) {
    return res.status(200).json({
      type: 'session_status_response',
      success: true,
      ...status
    });
  } else {
    return res.status(404).json({
      success: false,
      message: 'Session not found'
    });
  }
}

/**
 * Handle script shuffle requests
 * POST /api/join-session/shuffle
 */
async function handleShuffle(req, res) {
  const { session_id } = req.body;

  if (!session_id) {
    return res.status(400).json({
      success: false,
      message: 'session_id is required'
    });
  }

  const result = sessionManager.shuffleScriptAssignments(session_id);

  if (result.success) {
    return res.status(200).json({
      success: true,
      new_assignments: result.new_assignments,
      message: 'Scripts shuffled successfully'
    });
  } else {
    return res.status(400).json({
      success: false,
      message: result.message
    });
  }
}