/**
 * SP Crew Control V2 - Broadcasting API
 * Handles activity logging and message broadcasting
 */

const sessionManager = require('../lib/session-manager');

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).json({ message: 'OK' });
  }

  try {
    switch (req.method) {
      case 'POST':
        return await handleActivityBroadcast(req, res);
      case 'GET':
        return await handleActivityHistory(req, res);
      default:
        return res.status(405).json({ 
          success: false, 
          message: 'Method not allowed' 
        });
    }
  } catch (error) {
    console.error('Broadcast error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}

/**
 * Handle activity broadcasting
 * POST /api/broadcast
 */
async function handleActivityBroadcast(req, res) {
  const { session_id, activity } = req.body;

  // Validate required fields
  if (!session_id || !activity) {
    return res.status(400).json({
      success: false,
      message: 'session_id and activity are required'
    });
  }

  // Validate activity object
  const requiredActivityFields = ['remote_id', 'action'];
  const missingFields = requiredActivityFields.filter(field => !activity[field]);
  
  if (missingFields.length > 0) {
    return res.status(400).json({
      success: false,
      message: 'Missing required activity fields',
      missing_fields: missingFields
    });
  }

  // Validate action type
  const validActions = [
    'script_executed', 
    'mode_changed', 
    'joined_session', 
    'left_session',
    'button_pressed',
    'connection_lost',
    'connection_restored'
  ];
  
  if (!validActions.includes(activity.action)) {
    return res.status(400).json({
      success: false,
      message: `Invalid action. Must be one of: ${validActions.join(', ')}`
    });
  }

  // Log the activity
  const logEntry = sessionManager.logActivity(session_id, activity);

  if (logEntry) {
    return res.status(200).json({
      type: 'activity_log_broadcast',
      success: true,
      session_id: session_id,
      activity: logEntry,
      message: 'Activity logged and broadcasted'
    });
  } else {
    return res.status(404).json({
      success: false,
      message: 'Session not found'
    });
  }
}

/**
 * Handle activity history requests
 * GET /api/broadcast?session_id=xxx&limit=20
 */
async function handleActivityHistory(req, res) {
  const { session_id, limit } = req.query;

  if (!session_id) {
    return res.status(400).json({
      success: false,
      message: 'session_id parameter is required'
    });
  }

  const activityLimit = parseInt(limit) || 20;
  if (activityLimit < 1 || activityLimit > 100) {
    return res.status(400).json({
      success: false,
      message: 'limit must be between 1 and 100'
    });
  }

  const recentActivity = sessionManager.getRecentActivity(session_id, activityLimit);

  return res.status(200).json({
    success: true,
    session_id: session_id,
    activity_history: recentActivity,
    count: recentActivity.length,
    timestamp: new Date().toISOString()
  });
}

/**
 * Handle script execution logging
 * POST /api/broadcast/script-execution
 */
async function handleScriptExecution(req, res) {
  const { 
    session_id, 
    remote_id, 
    remote_name, 
    script_name, 
    success, 
    duration_ms, 
    error_message 
  } = req.body;

  // Validate required fields
  const requiredFields = ['session_id', 'remote_id', 'script_name', 'success'];
  const missingFields = requiredFields.filter(field => req.body[field] === undefined);
  
  if (missingFields.length > 0) {
    return res.status(400).json({
      success: false,
      message: 'Missing required fields',
      missing_fields: missingFields
    });
  }

  // Create activity entry
  const activity = {
    remote_id: remote_id,
    remote_name: remote_name || remote_id,
    action: 'script_executed',
    details: script_name,
    success: success,
    duration_ms: duration_ms,
    error_message: error_message
  };

  // Log the activity
  const logEntry = sessionManager.logActivity(session_id, activity);

  if (logEntry) {
    return res.status(200).json({
      type: 'script_execution_broadcast',
      success: true,
      session_id: session_id,
      activity: logEntry,
      message: `Script execution logged: ${script_name} (${success ? 'success' : 'failed'})`
    });
  } else {
    return res.status(404).json({
      success: false,
      message: 'Session not found'
    });
  }
}

/**
 * Handle connection status updates
 * POST /api/broadcast/connection-status
 */
async function handleConnectionStatus(req, res) {
  const { session_id, remote_id, remote_name, status, details } = req.body;

  // Validate required fields
  if (!session_id || !remote_id || !status) {
    return res.status(400).json({
      success: false,
      message: 'session_id, remote_id, and status are required'
    });
  }

  // Validate status
  const validStatuses = ['connected', 'disconnected', 'reconnecting', 'error'];
  if (!validStatuses.includes(status)) {
    return res.status(400).json({
      success: false,
      message: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
    });
  }

  // Create activity entry
  const activity = {
    remote_id: remote_id,
    remote_name: remote_name || remote_id,
    action: status === 'connected' ? 'connection_restored' : 'connection_lost',
    details: details || `Remote ${status}`,
    success: status === 'connected'
  };

  // Log the activity
  const logEntry = sessionManager.logActivity(session_id, activity);

  if (logEntry) {
    return res.status(200).json({
      type: 'connection_status_broadcast',
      success: true,
      session_id: session_id,
      activity: logEntry,
      message: `Connection status updated: ${remote_id} is ${status}`
    });
  } else {
    return res.status(404).json({
      success: false,
      message: 'Session not found'
    });
  }
}