import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL || 'https://qcefzjjxnwccjivsbtgb.supabase.co',
  process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

export default async function handler(req, res) {
  try {
    if (req.method === 'GET') {
      // Get all friendly names or specific ones
      const { script_names } = req.query;
      
      let query = supabase
        .from('script_friendly_names')
        .select('script_name, friendly_name, description');
      
      if (script_names) {
        const scriptList = script_names.split(',');
        query = query.in('script_name', scriptList);
      }
      
      const { data, error } = await query.order('friendly_name');
      
      if (error) {
        throw error;
      }
      
      // Convert to lookup object for easy access
      const friendlyNames = {};
      data?.forEach(item => {
        friendlyNames[item.script_name] = {
          friendly_name: item.friendly_name,
          description: item.description
        };
      });
      
      res.json({
        success: true,
        friendly_names: friendlyNames,
        count: data?.length || 0
      });
      
    } else if (req.method === 'POST') {
      // Add or update friendly name
      const { script_name, friendly_name, description } = req.body;
      
      if (!script_name || !friendly_name) {
        return res.status(400).json({
          success: false,
          error: 'script_name and friendly_name are required'
        });
      }
      
      const { data, error } = await supabase
        .from('script_friendly_names')
        .upsert({
          script_name,
          friendly_name,
          description: description || null
        })
        .select();
      
      if (error) {
        throw error;
      }
      
      res.json({
        success: true,
        message: 'Friendly name saved successfully',
        data: data[0]
      });
      
    } else if (req.method === 'DELETE') {
      // Delete friendly name
      const { script_name } = req.body;
      
      if (!script_name) {
        return res.status(400).json({
          success: false,
          error: 'script_name is required'
        });
      }
      
      const { error } = await supabase
        .from('script_friendly_names')
        .delete()
        .eq('script_name', script_name);
      
      if (error) {
        throw error;
      }
      
      res.json({
        success: true,
        message: 'Friendly name deleted successfully'
      });
      
    } else {
      res.status(405).json({
        success: false,
        error: 'Method not allowed'
      });
    }
    
  } catch (error) {
    console.error('Script friendly names API error:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Internal server error'
    });
  }
}