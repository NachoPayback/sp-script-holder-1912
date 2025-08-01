// Script execution API for SP Crew Control V2
// Vercel serverless function

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { hub_id, script_name, user_id } = req.body;

    if (!hub_id || !script_name || !user_id) {
      return res.status(400).json({ 
        error: 'hub_id, script_name, and user_id required' 
      });
    }

    // Insert command into script_commands table (triggers hub via real-time)
    const insertStartTime = Date.now();
    const { data: command, error: insertError } = await supabase
      .from('script_commands')
      .insert({
        hub_id,
        user_id,
        script_name,
        status: 'pending',
        created_at: new Date().toISOString() // Add timestamp for timing analysis
      })
      .select()
      .single();
    
    const insertDuration = Date.now() - insertStartTime;
    console.log(`[TIMING] Database insert took: ${insertDuration}ms`);

    if (insertError) {
      console.error('Insert error:', insertError);
      return res.status(500).json({ error: 'Failed to send command' });
    }

    const commandId = command.id;

    // Return command ID immediately - frontend will handle real-time result
    return res.status(200).json({
      success: true,
      commandId: commandId,
      message: 'Command sent to hub'
    });

  } catch (error) {
    console.error('Execute error:', error);
    return res.status(500).json({ error: 'Script execution failed' });
  }
}

// Removed polling function - frontend now handles real-time results