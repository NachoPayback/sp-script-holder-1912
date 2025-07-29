// Hub discovery API for SP Crew Control V2
// Vercel serverless function

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://qcefzjjxnwccjivsbtgb.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
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

  try {
    // Get hubs that have sent heartbeat in last 2 minutes
    const twoMinutesAgo = new Date(Date.now() - 2 * 60 * 1000).toISOString();
    
    const { data: hubs, error } = await supabase
      .table('hubs')
      .select('*')
      .gte('last_heartbeat', twoMinutesAgo)
      .eq('status', 'online');

    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Database error' });
    }

    const formattedHubs = hubs.map(hub => ({
      hub_id: hub.hub_id,
      hub_name: hub.hub_name,
      status: hub.status,
      script_count: hub.scripts ? hub.scripts.length : 0,
      scripts: hub.scripts || [],
      last_heartbeat: hub.last_heartbeat
    }));

    return res.status(200).json({
      success: true,
      hubs: formattedHubs,
      count: formattedHubs.length
    });

  } catch (error) {
    console.error('Hub discovery error:', error);
    return res.status(500).json({ error: 'Failed to discover hubs' });
  }
}