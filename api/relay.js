// Simple Vercel serverless function for SP Crew Control relay
// This single file handles all relay coordination

const hubs = new Map();
const sessions = new Map();

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { action } = req.query;

  try {
    switch (action) {
      case 'register-hub':
        return handleRegisterHub(req, res);
      
      case 'discover-hubs':
        return handleDiscoverHubs(req, res);
        
      case 'heartbeat':
        return handleHeartbeat(req, res);
        
      case 'create-session':
        return handleCreateSession(req, res);
        
      case 'join-session':
        return handleJoinSession(req, res);
        
      case 'broadcast':
        return handleBroadcast(req, res);
        
      default:
        return res.status(200).json({ 
          service: 'SP Crew Control Relay',
          status: 'online',
          endpoints: [
            '/api/relay?action=register-hub',
            '/api/relay?action=discover-hubs',
            '/api/relay?action=heartbeat&hub_id=xxx',
            '/api/relay?action=create-session',
            '/api/relay?action=join-session',
            '/api/relay?action=broadcast'
          ]
        });
    }
  } catch (error) {
    console.error('Relay error:', error);
    return res.status(500).json({ error: error.message });
  }
}

function handleRegisterHub(req, res) {
  const hubData = req.body;
  
  if (!hubData.hub_id) {
    return res.status(400).json({ error: 'hub_id required' });
  }
  
  hubs.set(hubData.hub_id, {
    ...hubData,
    registered_at: new Date().toISOString(),
    last_heartbeat: new Date().toISOString()
  });
  
  return res.status(200).json({ 
    success: true, 
    hub_id: hubData.hub_id,
    message: 'Hub registered successfully'
  });
}

function handleDiscoverHubs(req, res) {
  const activeHubs = [];
  const now = Date.now();
  
  for (const [hubId, hubInfo] of hubs.entries()) {
    const lastHeartbeat = new Date(hubInfo.last_heartbeat).getTime();
    if (now - lastHeartbeat < 120000) { // Active if heartbeat within 2 minutes
      activeHubs.push({
        hub_id: hubId,
        hub_name: hubInfo.hub_name,
        hub_location: hubInfo.hub_location,
        script_count: hubInfo.scripts?.length || 0
      });
    }
  }
  
  return res.status(200).json({
    success: true,
    hubs: activeHubs,
    count: activeHubs.length
  });
}

function handleHeartbeat(req, res) {
  const { hub_id } = req.query;
  
  if (!hub_id || !hubs.has(hub_id)) {
    return res.status(404).json({ error: 'Hub not found' });
  }
  
  const hub = hubs.get(hub_id);
  hub.last_heartbeat = new Date().toISOString();
  
  return res.status(200).json({ 
    success: true,
    message: 'Heartbeat recorded'
  });
}

function handleCreateSession(req, res) {
  const { hub_id, mode } = req.body;
  
  if (!hub_id) {
    return res.status(400).json({ error: 'hub_id required' });
  }
  
  const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  sessions.set(sessionId, {
    session_id: sessionId,
    hub_id: hub_id,
    mode: mode || 'single_button',
    created_at: new Date().toISOString(),
    remotes: []
  });
  
  return res.status(200).json({
    success: true,
    session_id: sessionId
  });
}

function handleJoinSession(req, res) {
  const { session_id, remote_id, remote_name } = req.body;
  
  if (!session_id || !sessions.has(session_id)) {
    return res.status(404).json({ error: 'Session not found' });
  }
  
  const session = sessions.get(session_id);
  
  // Add remote to session if not already there
  if (!session.remotes.find(r => r.remote_id === remote_id)) {
    session.remotes.push({
      remote_id,
      remote_name,
      joined_at: new Date().toISOString()
    });
  }
  
  return res.status(200).json({
    success: true,
    session: session
  });
}

function handleBroadcast(req, res) {
  const { session_id, type, data } = req.body;
  
  // In a real implementation, this would push to WebSockets
  // For now, just log and acknowledge
  console.log(`Broadcast to session ${session_id}:`, type, data);
  
  return res.status(200).json({
    success: true,
    message: 'Broadcast sent'
  });
}