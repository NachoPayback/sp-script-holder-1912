// Script execution API for SP Crew Control V2
// Vercel serverless function

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  'https://qcefzjjxnwccjivsbtgb.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
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
    const { data: command, error: insertError } = await supabase
      .from('script_commands')
      .insert({
        hub_id,
        user_id,
        script_name,
        status: 'pending'
      })
      .select()
      .single();

    if (insertError) {
      console.error('Insert error:', insertError);
      return res.status(500).json({ error: 'Failed to send command' });
    }

    const commandId = command.id;

    // Wait for result with timeout
    const result = await waitForResult(commandId, 35000); // 35 second timeout

    return res.status(200).json(result);

  } catch (error) {
    console.error('Execute error:', error);
    return res.status(500).json({ error: 'Script execution failed' });
  }
}

async function waitForResult(commandId, timeout = 35000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      // Check for result in script_results table
      const { data: results, error } = await supabase
        .from('script_results')
        .select('*')
        .eq('command_id', commandId)
        .limit(1);

      if (error) {
        console.error('Result query error:', error);
        break;
      }

      if (results && results.length > 0) {
        const result = results[0];
        return {
          success: result.success,
          output: result.stdout,
          error: result.stderr,
          duration_ms: 0 // We don't track duration in new format yet
        };
      }

      // Also check command status for early failure detection
      const { data: commands, error: cmdError } = await supabase
        .from('script_commands')
        .select('status')
        .eq('id', commandId)
        .limit(1);

      if (!cmdError && commands && commands.length > 0) {
        const status = commands[0].status;
        
        // If command failed without creating a result record
        if (status === 'failed') {
          return { 
            success: false, 
            error: 'Script execution failed (no result recorded)',
            output: ''
          };
        }
      }

      // Wait 100ms before checking again
      await new Promise(resolve => setTimeout(resolve, 100));
      
    } catch (error) {
      console.error('Error waiting for result:', error);
      break;
    }
  }
  
  return { success: false, error: 'Execution timeout' };
}