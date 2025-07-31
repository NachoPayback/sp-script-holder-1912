// Hub scripts API for SP Crew Control V2
// Gets available scripts for a hub

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
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
    // Get scripts from hub_scripts table with friendly names
    const { data: scripts, error } = await supabase
      .from('hub_scripts')
      .select('script_name, friendly_name')
      .eq('hub_id', hub_id);

    if (error) {
      console.error('Error fetching scripts:', error);
      return res.status(500).json({ error: 'Database error' });
    }

    // If no scripts in hub_scripts table, fall back to hub's scripts column
    if (!scripts || scripts.length === 0) {
      const { data: hub, error: hubError } = await supabase
        .from('hubs')
        .select('scripts')
        .eq('id', hub_id)
        .single();

      if (hubError) {
        console.error('Error fetching hub:', hubError);
        return res.status(500).json({ error: 'Database error' });
      }

      // Extract script names from legacy format
      const legacyScripts = hub.scripts || [];
      const scriptNames = legacyScripts.map(s => s.name || s);

      return res.status(200).json({
        success: true,
        scripts: scriptNames
      });
    }

    return res.status(200).json({
      success: true,
      scripts: scripts.map(s => ({
        script_name: s.script_name,
        friendly_name: s.friendly_name || s.script_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      }))
    });

  } catch (error) {
    console.error('Hub scripts API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}