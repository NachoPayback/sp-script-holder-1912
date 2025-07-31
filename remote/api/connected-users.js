// Get connected users for a hub
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL || 'https://qcefzjjxnwccjivsbtgb.supabase.co',
  process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { hub_id } = req.query;

  if (!hub_id) {
    return res.status(400).json({ error: 'hub_id required' });
  }

  try {
    // Get active remotes for this hub (users currently connected)
    const { data: activeRemotes, error } = await supabase
      .from('active_remotes')
      .select('user_id, connected_at')
      .eq('hub_id', hub_id)
      .gte('connected_at', new Date(Date.now() - 5 * 60 * 1000).toISOString()); // Active in last 5 minutes

    if (error) {
      console.error('Database error:', error);
      return res.status(500).json({ error: 'Database error' });
    }

    // Extract unique user IDs and clean them up to show as usernames
    const connectedUsers = activeRemotes.map(remote => {
      // Convert user IDs like 'user-abc123' to cleaner display names
      const userId = remote.user_id;
      if (userId.startsWith('user-')) {
        return `User-${userId.split('-')[1].toUpperCase()}`;
      }
      return userId;
    });

    return res.status(200).json({
      success: true,
      users: [...new Set(connectedUsers)], // Remove duplicates
      count: connectedUsers.length
    });

  } catch (error) {
    console.error('Connected users error:', error);
    return res.status(500).json({ error: 'Failed to get connected users' });
  }
}