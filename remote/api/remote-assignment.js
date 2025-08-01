// Remote assignment API for SP Crew Control V2
// Handles getting and setting script assignments for remotes

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL || 'https://qcefzjjxnwccjivsbtgb.supabase.co',
  process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { hub_id, user_id } = req.query;

  if (!hub_id || !user_id) {
    return res.status(400).json({ error: 'hub_id and user_id required' });
  }

  try {
    if (req.method === 'GET') {
      // Get current assignment
      const { data: assignment, error } = await supabase
        .from('active_remotes')
        .select('*')
        .eq('hub_id', hub_id)
        .eq('user_id', user_id)
        .single();

      if (error && error.code !== 'PGRST116') { // Not found is ok
        console.error('Error fetching assignment:', error);
        return res.status(500).json({ error: 'Database error' });
      }

      return res.status(200).json({
        success: true,
        assignment: assignment || null
      });

    } else if (req.method === 'POST') {
      // Create or update assignment (triggers hub to assign script)
      const { data, error } = await supabase
        .from('active_remotes')
        .upsert({
          hub_id,
          user_id,
          last_seen: new Date().toISOString()
        }, {
          onConflict: 'hub_id,user_id'
        })
        .select()
        .single();

      if (error) {
        console.error('Error creating assignment:', error);
        return res.status(500).json({ error: 'Failed to create assignment' });
      }

      return res.status(200).json({
        success: true,
        assignment: data
      });

    } else {
      return res.status(405).json({ error: 'Method not allowed' });
    }

  } catch (error) {
    console.error('Assignment API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}