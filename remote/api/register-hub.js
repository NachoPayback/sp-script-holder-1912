// Hub registration API for SP Crew Control V2
// Allows hub workers to register themselves with the database

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
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