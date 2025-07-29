/**
 * SP Crew Control V2 - Hub Discovery API
 * Handles hub registration and discovery requests
 */

const sessionManager = require('../lib/session-manager');

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).json({ message: 'OK' });
  }

  try {
    switch (req.method) {
      case 'POST':
        return await handleHubRegistration(req, res);
      case 'GET':
        return await handleHubDiscovery(req, res);
      default:
        return res.status(405).json({ 
          success: false, 
          message: 'Method not allowed' 
        });
    }
  } catch (error) {
    console.error('Hub discovery error:', error);
    return res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}

/**
 * Handle hub registration requests
 * POST /api/discover-hubs
 */
async function handleHubRegistration(req, res) {
  const hubData = req.body;

  // Validate required fields
  const requiredFields = ['hub_id', 'hub_name', 'scripts', 'websocket_url'];
  const missingFields = requiredFields.filter(field => !hubData[field]);
  
  if (missingFields.length > 0) {
    return res.status(400).json({
      success: false,
      message: 'Missing required fields',
      missing_fields: missingFields
    });
  }

  // Validate hub_id format
  if (!/^[a-zA-Z0-9_-]+$/.test(hubData.hub_id)) {
    return res.status(400).json({
      success: false,
      message: 'Invalid hub_id format. Use only alphanumeric characters, underscores, and hyphens.'
    });
  }

  // Validate scripts array
  if (!Array.isArray(hubData.scripts)) {
    return res.status(400).json({
      success: false,
      message: 'Scripts must be an array'
    });
  }

  // Validate each script object
  for (const script of hubData.scripts) {
    if (!script.name || !script.display_name) {
      return res.status(400).json({
        success: false,
        message: 'Each script must have name and display_name fields'
      });
    }
  }

  // Validate websocket URL
  if (!hubData.websocket_url.startsWith('ws://') && !hubData.websocket_url.startsWith('wss://')) {
    return res.status(400).json({
      success: false,
      message: 'websocket_url must start with ws:// or wss://'
    });
  }

  // Set defaults
  const processedHubData = {
    ...hubData,
    max_remotes: hubData.max_remotes || 6,
    hub_location: hubData.hub_location || 'Unknown Location'
  };

  // Register hub
  const result = sessionManager.registerHub(processedHubData);

  if (result.success) {
    return res.status(200).json({
      success: true,
      message: 'Hub registered successfully',
      hub_id: result.hub_id,
      registered_at: new Date().toISOString()
    });
  } else {
    return res.status(400).json(result);
  }
}

/**
 * Handle hub discovery requests  
 * GET /api/discover-hubs
 */
async function handleHubDiscovery(req, res) {
  const availableHubs = sessionManager.getAvailableHubs();

  // Clean up inactive sessions periodically
  const cleanedSessions = sessionManager.cleanupInactiveSessions();
  if (cleanedSessions > 0) {
    console.log(`Cleaned up ${cleanedSessions} inactive sessions`);
  }

  return res.status(200).json({
    success: true,
    hubs: availableHubs,
    timestamp: new Date().toISOString(),
    total_hubs: availableHubs.length
  });
}

/**
 * Hub heartbeat endpoint
 * PUT /api/discover-hubs/:hubId/heartbeat
 */
async function handleHeartbeat(req, res) {
  const { hubId } = req.query;

  if (!hubId) {
    return res.status(400).json({
      success: false,
      message: 'Hub ID required'
    });
  }

  const success = sessionManager.updateHubHeartbeat(hubId);

  if (success) {
    return res.status(200).json({
      success: true,
      message: 'Heartbeat updated',
      timestamp: new Date().toISOString()
    });
  } else {
    return res.status(404).json({
      success: false,
      message: 'Hub not found'
    });
  }
}