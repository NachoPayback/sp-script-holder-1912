/**
 * SP Crew Control V2 - Message Relay Status API
 * Provides status information about the relay service
 */

const sessionManager = require('../lib/session-manager');

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).json({ message: 'OK' });
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ 
      success: false, 
      message: 'Method not allowed' 
    });
  }

  try {
    // Get current system status
    const availableHubs = sessionManager.getAvailableHubs();
    const activeSessions = Array.from(sessionManager.sessions.values())
      .filter(session => session.status === 'active');
    const totalRemotes = sessionManager.remotes.size;

    // Calculate uptime (simplified - in production would track actual start time)
    const uptimeSeconds = Math.floor(process.uptime());
    
    // Memory usage
    const memoryUsage = process.memoryUsage();

    const status = {
      service: 'SP Crew Control V2 Message Relay',
      version: '2.0.0',
      status: 'operational',
      timestamp: new Date().toISOString(),
      uptime: {
        seconds: uptimeSeconds,
        human: formatUptime(uptimeSeconds)
      },
      statistics: {
        registered_hubs: availableHubs.length,
        active_sessions: activeSessions.length,
        connected_remotes: totalRemotes,
        total_activity_logs: activeSessions.reduce((total, session) => 
          total + (session.activity_log?.length || 0), 0)
      },
      hub_summary: availableHubs.map(hub => ({
        hub_id: hub.hub_id,
        hub_name: hub.hub_name,
        hub_location: hub.hub_location,
        connected_remotes: hub.connected_remotes,
        max_remotes: hub.max_remotes,
        latency_ms: hub.latency_ms
      })),
      session_summary: activeSessions.map(session => ({
        session_id: session.session_id,
        hub_id: session.hub_id,
        current_mode: session.current_mode,
        connected_remotes: session.connected_remotes.length,
        created_at: session.created_at
      })),
      system_health: {
        memory: {
          used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024),
          total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024),
          external_mb: Math.round(memoryUsage.external / 1024 / 1024)
        },
        node_version: process.version,
        platform: process.platform
      },
      endpoints: {
        hub_discovery: '/api/discover-hubs',
        session_management: '/api/join-session',
        activity_broadcasting: '/api/broadcast',
        status: '/api/status'
      }
    };

    return res.status(200).json(status);

  } catch (error) {
    console.error('Status endpoint error:', error);
    return res.status(500).json({
      service: 'SP Crew Control V2 Message Relay',
      status: 'error',
      timestamp: new Date().toISOString(),
      error: 'Failed to retrieve status',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Internal server error'
    });
  }
}

/**
 * Format uptime seconds into human readable string
 */
function formatUptime(seconds) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

  return parts.join(' ');
}