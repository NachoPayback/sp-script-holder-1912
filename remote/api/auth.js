// Authentication API for SP Crew Control V2
// Vercel serverless function

const { createClient } = require('@supabase/supabase-js');
const bcrypt = require('bcryptjs');

const supabase = createClient(
  process.env.SUPABASE_URL || 'https://qcefzjjxnwccjivsbtgb.supabase.co',
  process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

// Users are stored securely in Supabase database

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // Handle getUserPermissions request
    const { username } = req.query;
    
    if (!username) {
      return res.status(400).json({ error: 'Username required' });
    }
    
    try {
      // Get user permissions from Supabase database
      const { data: users, error } = await supabase
        .from('users')
        .select('username, permissions')
        .eq('username', username)
        .limit(1);

      if (error || !users || users.length === 0) {
        return res.status(404).json({ success: false, error: 'User not found' });
      }

      const user = users[0];
      
      return res.status(200).json({
        success: true,
        permissions: user.permissions || {}
      });
      
    } catch (error) {
      console.error('Get user permissions error:', error);
      return res.status(500).json({ success: false, error: 'Failed to get user permissions' });
    }
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { username, password, token } = req.body;

    // Handle token verification
    if (token) {
      try {
        const decoded = JSON.parse(Buffer.from(token, 'base64').toString());
        
        if (decoded.expires < Date.now()) {
          return res.status(401).json({ valid: false, error: 'Token expired' });
        }
        
        // Get user from database to verify token is still valid
        const { data: users, error } = await supabase
          .from('users')
          .select('username, permissions')
          .eq('username', decoded.username)
          .limit(1);

        if (error || !users || users.length === 0) {
          return res.status(401).json({ valid: false, error: 'Invalid token' });
        }

        const user = users[0];
        
        return res.status(200).json({
          valid: true,
          user: {
            username: user.username,
            permissions: user.permissions
          }
        });
        
      } catch (error) {
        return res.status(401).json({ valid: false, error: 'Invalid token format' });
      }
    }

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password required' });
    }

    // Get user from Supabase database
    const { data: users, error } = await supabase
      .from('users')
      .select('*')
      .eq('username', username)
      .limit(1);

    if (error || !users || users.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = users[0];

    // Verify password (plain text comparison for now - should use bcrypt in production)
    if (password !== user.password_plain) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate simple session token (username + timestamp + random)
    const sessionToken = Buffer.from(
      JSON.stringify({
        username,
        permissions: user.permissions,
        expires: Date.now() + (24 * 60 * 60 * 1000), // 24 hours
        random: Math.random().toString(36).substring(7)
      })
    ).toString('base64');

    console.log(`User ${username} authenticated successfully`);

    return res.status(200).json({
      success: true,
      token: sessionToken,
      user: {
        username,
        permissions: user.permissions
      }
    });

  } catch (error) {
    console.error('Auth error:', error);
    return res.status(500).json({ error: 'Authentication failed' });
  }
}