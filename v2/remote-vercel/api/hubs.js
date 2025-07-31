// Hub discovery API for SP Crew Control V2
// Vercel serverless function

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

  // Debug environment variables
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
    return res.status(500).json({ 
      error: 'Missing environment variables',
      hasUrl: !!process.env.SUPABASE_URL,
      hasKey: !!process.env.SUPABASE_ANON_KEY
    });
  }

  try {
    console.log('Attempting to fetch hubs from Supabase...');
    
    // Get hubs with status online from database
    const { data: hubs, error } = await supabase
      .from('hubs')
      .select('*')
      .eq('status', 'online')
      .limit(10);
    
    console.log('Supabase response:', { hubs, error });
    
    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ 
        error: 'Database error', 
        details: error.message,
        code: error.code 
      });
    }
    
    // Filter out stale hubs (no heartbeat for more than 2 minutes)
    const now = new Date();
    console.log('Current time:', now.toISOString());
    
    const activeHubs = (hubs || []).filter(hub => {
      if (!hub.last_seen) {
        console.log(`Hub ${hub.id} has no last_seen`);
        return false;
      }
      const lastSeen = new Date(hub.last_seen);
      const timeDiff = (now - lastSeen) / 1000; // seconds
      console.log(`Hub ${hub.id}: last_seen=${hub.last_seen}, timeDiff=${timeDiff}s`);
      return timeDiff < 30; // Less than 30 seconds for testing
    });
    
    console.log(`Found ${hubs?.length || 0} total hubs, ${activeHubs.length} active`);

    // Get script count for each active hub
    const hubsWithScripts = await Promise.all(
      activeHubs.map(async (hub) => {
        const { data: scripts } = await supabase
          .from('hub_scripts')
          .select('script_name')
          .eq('hub_id', hub.id);
        
        return {
          id: hub.id,
          machine_id: hub.machine_id,
          friendly_name: hub.friendly_name,
          status: hub.status || 'online',
          scripts: scripts?.map(s => s.script_name) || [],
          script_count: scripts?.length || 0,
          mode: hub.mode || 'shared',
          show_script_names: hub.show_script_names || false,
          last_heartbeat: new Date().toISOString()
        };
      })
    );
    
    return res.status(200).json({
      success: true,
      hubs: hubsWithScripts,
      count: hubsWithScripts.length
    });

  } catch (error) {
    console.error('Hub discovery error:', error);
    return res.status(500).json({ error: 'Failed to discover hubs' });
  }
}