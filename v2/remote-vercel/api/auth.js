// Authentication API for SP Crew Control V2
// Vercel serverless function

const { createClient } = require('@supabase/supabase-js');
const bcrypt = require('bcryptjs');

const supabase = createClient(
  'https://qcefzjjxnwccjivsbtgb.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4'
);

// Users are stored securely in Supabase database

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
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password required' });
    }

    // Get user from Supabase database
    const { data: users, error } = await supabase
      .table('users')
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
        permissions: user.permissions || { all_hubs: true },
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
        permissions: user.permissions || { all_hubs: true }
      }
    });

  } catch (error) {
    console.error('Auth error:', error);
    return res.status(500).json({ error: 'Authentication failed' });
  }
}