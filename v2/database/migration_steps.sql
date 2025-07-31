-- FULL MIGRATION to V2 Remote Hub System
-- Run ALL these commands in Supabase SQL Editor

-- Step 1: Create new hubs table with correct structure
CREATE TABLE hubs_new (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  machine_id TEXT UNIQUE NOT NULL,
  friendly_name TEXT,
  status TEXT DEFAULT 'offline',
  mode TEXT DEFAULT 'shared',
  show_script_names BOOLEAN DEFAULT false,
  auto_shuffle_enabled BOOLEAN DEFAULT false,
  auto_shuffle_interval INTEGER DEFAULT 300,
  last_seen TIMESTAMP DEFAULT NOW(),
  dependencies_ready BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Step 2: Migrate data from old table (if it exists)
INSERT INTO hubs_new (machine_id, friendly_name, status, last_seen)
SELECT 
  COALESCE(hub_id, 'unknown-' || random()::text) as machine_id,
  COALESCE(hub_name, 'Unknown Hub') as friendly_name,
  COALESCE(status, 'offline') as status,
  COALESCE(last_heartbeat, NOW()) as last_seen
FROM hubs
ON CONFLICT (machine_id) DO UPDATE SET
  friendly_name = EXCLUDED.friendly_name,
  status = EXCLUDED.status,
  last_seen = EXCLUDED.last_seen;

-- Step 3: Drop old table and rename new one
DROP TABLE IF EXISTS hubs CASCADE;
ALTER TABLE hubs_new RENAME TO hubs;

-- Step 4: Create new tables
CREATE TABLE hub_scripts (
  hub_id UUID REFERENCES hubs(id) ON DELETE CASCADE,
  script_name TEXT,
  discovered_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (hub_id, script_name)
);

CREATE TABLE active_remotes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hub_id UUID REFERENCES hubs(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  assigned_script TEXT,
  script_color TEXT,
  connected_at TIMESTAMP DEFAULT NOW(),
  last_seen TIMESTAMP DEFAULT NOW(),
  UNIQUE(hub_id, user_id)
);

-- Step 5: Update script_commands table to use UUID hub_id
ALTER TABLE script_commands DROP CONSTRAINT IF EXISTS script_commands_hub_id_fkey;
ALTER TABLE script_commands ALTER COLUMN hub_id TYPE UUID USING hub_id::UUID;
ALTER TABLE script_commands ADD CONSTRAINT script_commands_hub_id_fkey 
  FOREIGN KEY (hub_id) REFERENCES hubs(id) ON DELETE CASCADE;
ALTER TABLE script_commands ADD COLUMN IF NOT EXISTS user_id TEXT;

-- Step 6: Update script_results table structure
ALTER TABLE script_results DROP CONSTRAINT IF EXISTS script_results_message_id_fkey;
ALTER TABLE script_results RENAME COLUMN message_id TO command_id;
ALTER TABLE script_results ADD CONSTRAINT script_results_command_id_fkey 
  FOREIGN KEY (command_id) REFERENCES script_commands(id) ON DELETE CASCADE;

-- Step 7: Enable real-time on all tables
ALTER TABLE hubs REPLICA IDENTITY FULL;
ALTER TABLE hub_scripts REPLICA IDENTITY FULL;
ALTER TABLE active_remotes REPLICA IDENTITY FULL;
ALTER TABLE script_commands REPLICA IDENTITY FULL;
ALTER TABLE script_results REPLICA IDENTITY FULL;

-- Step 8: Create indexes
CREATE INDEX idx_hubs_machine_id ON hubs(machine_id);
CREATE INDEX idx_hubs_status ON hubs(status);
CREATE INDEX idx_active_remotes_hub_user ON active_remotes(hub_id, user_id);
CREATE INDEX idx_script_commands_hub_status ON script_commands(hub_id, status);