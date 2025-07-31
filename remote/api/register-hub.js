// Hub registration API for SP Crew Control V2
// Allows hub workers to register themselves with the database

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://qcefzjjxnwccjivsbtgb.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { hub_id, hub_name, scripts } = req.body;

    if (!hub_id || !hub_name || !scripts) {
      return res.status(400).json({ 
        error: 'hub_id, hub_name, and scripts required' 
      });
    }

    // Register/update hub in database
    const { data: hub, error } = await supabase
      .from('hubs')
      .upsert({
        hub_id,
        hub_name,
        status: 'online',
        scripts,
        last_heartbeat: new Date().toISOString(),
        created_at: new Date().toISOString()
      }, { 
        onConflict: 'hub_id' 
      })
      .select()
      .single();

    if (error) {
      console.error('Hub registration error:', error);
      return res.status(500).json({ error: 'Failed to register hub' });
    }

    console.log(`Hub registered: ${hub_id} (${hub_name})`);

    return res.status(200).json({
      success: true,
      message: 'Hub registered successfully',
      hub_id: hub.hub_id
    });

  } catch (error) {
    console.error('Registration error:', error);
    return res.status(500).json({ error: 'Hub registration failed' });
  }
}