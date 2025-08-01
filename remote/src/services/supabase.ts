import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://qcefzjjxnwccjivsbtgb.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjZWZ6amp4bndjY2ppdnNidGdiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4MjA4OTIsImV4cCI6MjA2OTM5Njg5Mn0.qAW4A2-RVg114QiAnJF3KMXrySIYu9EKHNrhWgpibS4';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Re-export types
export type { RealtimeChannel } from '@supabase/supabase-js';