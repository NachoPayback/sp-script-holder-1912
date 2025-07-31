# Remote Hub System - Clean Architecture

## Overview
A system where remotes (web interfaces) connect to hubs (local Python apps) to execute scripts. Remotes get big "PRESS" buttons that trigger scripts on the connected hub.

## Database Schema (Supabase Extensions)

### Extend Existing Tables

```sql
-- Add columns to existing hubs table
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS mode TEXT DEFAULT 'shared';
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'offline';
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS friendly_name TEXT;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS show_script_names BOOLEAN DEFAULT false;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS auto_shuffle_enabled BOOLEAN DEFAULT false;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS auto_shuffle_interval INTEGER DEFAULT 300;
-- Complete database schema with all missing pieces
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS mode TEXT DEFAULT 'shared';
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'offline';
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS friendly_name TEXT;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS show_script_names BOOLEAN DEFAULT false;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS auto_shuffle_enabled BOOLEAN DEFAULT false;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS auto_shuffle_interval INTEGER DEFAULT 300;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS shuffle_countdown INTEGER DEFAULT 0;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS dependencies_ready BOOLEAN DEFAULT false;
ALTER TABLE hubs ADD COLUMN IF NOT EXISTS last_shuffle TIMESTAMP DEFAULT NOW();
ALTER TABLE hubs ADD CONSTRAINT unique_machine_id UNIQUE (machine_id);

-- Track available scripts per hub
CREATE TABLE hub_scripts (
  hub_id UUID REFERENCES hubs(id) ON DELETE CASCADE,
  script_name TEXT,
  discovered_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (hub_id, script_name)
);

-- New table for hub commands (like update requests)
CREATE TABLE hub_commands (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hub_id UUID REFERENCES hubs(id) ON DELETE CASCADE,
  action TEXT NOT NULL, -- 'update_scripts', etc.
  requested_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Enable real-time subscriptions on all tables
ALTER TABLE hubs REPLICA IDENTITY FULL;
ALTER TABLE active_remotes REPLICA IDENTITY FULL;
ALTER TABLE script_commands REPLICA IDENTITY FULL;
ALTER TABLE script_results REPLICA IDENTITY FULL;
ALTER TABLE script_usage REPLICA IDENTITY FULL;
ALTER TABLE hub_commands REPLICA IDENTITY FULL;
ALTER TABLE hub_scripts REPLICA IDENTITY FULL;
```

### New Tables

```sql
-- Track active remote connections and their script assignments
CREATE TABLE active_remotes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hub_id UUID REFERENCES hubs(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  assigned_script TEXT,
  script_color TEXT, -- hex color for the button
  connected_at TIMESTAMP DEFAULT NOW(),
  last_seen TIMESTAMP DEFAULT NOW(),
  UNIQUE(hub_id, user_id)
);

-- Fair script distribution tracking
CREATE TABLE script_usage (
  hub_id UUID REFERENCES hubs(id) ON DELETE CASCADE,
  script_name TEXT,
  usage_count INTEGER DEFAULT 0,
  last_used TIMESTAMP,
  PRIMARY KEY (hub_id, script_name)
);

-- Enable real-time subscriptions
ALTER TABLE hubs REPLICA IDENTITY FULL;
ALTER TABLE active_remotes REPLICA IDENTITY FULL;
ALTER TABLE script_commands REPLICA IDENTITY FULL;
ALTER TABLE script_results REPLICA IDENTITY FULL;
```

## Hub (Python Application)

### Hub Registration & Startup

```python
import os
import psutil
import socket
from supabase import create_client, Client

class Hub:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.hub_id = None
        self.available_scripts = []
        self.shuffle_timer = None
        self.shuffle_countdown = 0
        self.dependencies_ready = False
        

        
    def update_scripts_from_git(self):
        """Pull latest scripts from git repository with authentication"""
        try:
            # Set git credentials if needed (use environment variables)
            if GIT_USERNAME and GIT_TOKEN:
                # Configure git credentials for private repos
                subprocess.run([
                    'git', 'config', 'credential.helper', 
                    f'!f() {{ echo "username={GIT_USERNAME}"; echo "password={GIT_TOKEN}"; }}; f'
                ], capture_output=True)
            
            result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Scripts updated from git")
                # Clear any pending script commands since scripts changed
                self.supabase.table('script_commands').delete().eq('hub_id', self.hub_id).eq('status', 'pending').execute()
            else:
                print(f"Git pull failed: {result.stderr}")
        except Exception as e:
            print(f"Error updating from git: {e}")
            
    def listen_for_update_requests(self):
        """Listen for remote-triggered script updates"""
        def handle_update_request(payload):
            if payload['new']['hub_id'] == self.hub_id and payload['new']['action'] == 'update_scripts':
                print("Update requested by remote...")
                self.update_scripts_from_git()
                self.discover_scripts()
                self.preinstall_all_dependencies()
                
                # Mark dependencies as ready
                self.dependencies_ready = True
                self.supabase.table('hubs').update({
                    'dependencies_ready': True
                }).eq('id', self.hub_id).execute()
                
        # Subscribe to hub_commands table for update requests
        self.supabase.table('hub_commands').on('INSERT', handle_update_request).subscribe()
        
    def start_heartbeat(self):
        """Update hub status every 30 seconds"""
        def heartbeat():
            while not self.shutdown_requested:
                try:
                    self.supabase.table('hubs').update({
                        'status': 'online',
                        'last_seen': 'now()'
                    }).eq('id', self.hub_id).execute()
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                time.sleep(30)
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
        
    def start_shuffle_timer(self):
        """Start auto-shuffle timer if enabled"""
        def shuffle_loop():
            while not self.shutdown_requested:
                try:
                    # Get current hub settings
                    hub_data = self.supabase.table('hubs').select('auto_shuffle_enabled', 'auto_shuffle_interval').eq('id', self.hub_id).single().execute()
                    
                    if hub_data.data['auto_shuffle_enabled']:
                        interval = hub_data.data['auto_shuffle_interval']
                        
                        # Countdown timer
                        for countdown in range(interval, 0, -1):
                            if self.shutdown_requested:
                                break
                            self.shuffle_countdown = countdown
                            # Broadcast countdown to remotes
                            self.supabase.table('hubs').update({
                                'shuffle_countdown': countdown
                            }).eq('id', self.hub_id).execute()
                            time.sleep(1)
                        
                        # Trigger shuffle
                        if not self.shutdown_requested:
                            self.shuffle_assignments()
                    else:
                        time.sleep(5)  # Check settings every 5 seconds when disabled
                except Exception as e:
                    print(f"Shuffle timer error: {e}")
                    time.sleep(5)
        
        shuffle_thread = threading.Thread(target=shuffle_loop, daemon=True)
        shuffle_thread.start()
        
    def listen_for_commands(self):
        """Subscribe to script commands via Supabase real-time"""
        
        def handle_command(payload):
            command_data = payload['new']
            if command_data['hub_id'] == self.hub_id and command_data['status'] == 'pending':
                # Execute in separate thread to avoid blocking
                execution_thread = threading.Thread(target=self.execute_script, args=(command_data,))
                execution_thread.start()
        
        # Subscribe to script_commands table
        self.supabase.table('script_commands').on('INSERT', handle_command).subscribe()
        
    def register_hub(self):
        """Register or update hub in database on startup"""
        machine_name = socket.gethostname()
        hub_data = {
            'machine_id': self.get_machine_id(),
            'friendly_name': f"Hub-{machine_name}",
            'status': 'online',
            'last_seen': 'now()'
        }
        
        # Upsert hub registration
        result = self.supabase.table('hubs').upsert(
            hub_data, 
            on_conflict='machine_id'
        ).execute()
        
        self.hub_id = result.data[0]['id']
        print(f"Hub registered with ID: {self.hub_id}")
        
    def discover_scripts(self):
        """Scan scripts directory for available scripts"""
        scripts_dir = "scripts"
        self.available_scripts = []
        
        for item in os.listdir(scripts_dir):
            script_path = os.path.join(scripts_dir, item)
            if os.path.isdir(script_path):
                # Look for script.py in subdirectory
                main_script = os.path.join(script_path, "script.py")
                if os.path.exists(main_script):
                    self.available_scripts.append(item)
        
        print(f"Found scripts: {self.available_scripts}")
```



def assign_script_to_remote(self, user_id):
    """Assign a script avoiding conflicts with other active remotes"""
    
    try:
        # Clean up disconnected remotes first
        self.cleanup_disconnected_remotes()
        
        if not self.available_scripts:
            print(f"No scripts available to assign to user {user_id}")
            return None, None
        
        # Get currently assigned scripts to avoid conflicts
        active_assignments = self.supabase.table('active_remotes').select('assigned_script').eq('hub_id', self.hub_id).execute()
        currently_assigned = [row['assigned_script'] for row in active_assignments.data if row['assigned_script']]
        
        # Get usage counts for fair distribution
        usage_data = self.supabase.table('script_usage').select('*').eq('hub_id', self.hub_id).execute()
        usage_map = {row['script_name']: row['usage_count'] for row in usage_data.data}
        
        # Find available script folders (not currently assigned to other remotes)
        available_folders = [folder for folder in self.available_scripts if folder not in currently_assigned]
        
        # If all scripts assigned, fall back to least used
        if not available_folders:
            min_usage = min([usage_map.get(folder, 0) for folder in self.available_scripts])
            available_folders = [folder for folder in self.available_scripts 
                                if usage_map.get(folder, 0) == min_usage]
        
        # Random selection from available script folders
        import random
        selected_folder = random.choice(available_folders)
        script_color = f"#{random.randint(0x100000, 0xFFFFFF):06x}"
        
        # Update active_remotes table with folder name
        self.supabase.table('active_remotes').upsert({
            'hub_id': self.hub_id,
            'user_id': user_id,
            'assigned_script': selected_folder,  # Store folder name
            'script_color': script_color,
            'last_seen': 'now()'
        }, on_conflict='hub_id,user_id').execute()
        
        print(f"Assigned script {selected_folder} to user {user_id}")
        return selected_folder, script_color
        
    except Exception as e:
        print(f"Error assigning script to user {user_id}: {e}")
        return None, None

def listen_for_remote_connections(self):
    """Listen for new remote connections and assign scripts"""
    def handle_remote_connection(payload):
        try:
            if payload.new['hub_id'] == self.hub_id:
                user_id = payload.new['user_id']
                
                # Get hub mode
                hub_data = self.supabase.table('hubs').select('mode').eq('id', self.hub_id).single().execute()
                
                # Only assign scripts in assigned mode and if no script assigned yet
                if hub_data.data['mode'] == 'assigned' and not payload.new.get('assigned_script'):
                    self.assign_script_to_remote(user_id)
        except Exception as e:
            print(f"Error handling remote connection: {e}")
    
    # Subscribe to active_remotes table for new connections
    self.supabase.table('active_remotes').on('INSERT', handle_remote_connection).subscribe()
    self.supabase.table('active_remotes').on('UPDATE', handle_remote_connection).subscribe()

def shuffle_assignments(self):
    """Reassign scripts to all connected remotes and notify them"""
    active_remotes = self.supabase.table('active_remotes').select('user_id').eq('hub_id', self.hub_id).execute()
    
    for remote in active_remotes.data:
        self.assign_script_to_remote(remote['user_id'])
    
    # Trigger frontend update by updating hub timestamp
    self.supabase.table('hubs').update({
        'last_shuffle': 'now()'
    }).eq('id', self.hub_id).execute()
    
    print("Scripts shuffled for all connected remotes")
```

## Remote Frontend (TypeScript/React)

### Complete Remote Interface

```typescript
import React, { useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

interface RemoteState {
  selectedHub: string | null;
  hubMode: 'assigned' | 'shared';
  assignedScript?: string;
  scriptColor?: string;
  showScriptNames: boolean;
  availableScripts: string[];
  hubReady: boolean;
}

// Get user ID from Supabase auth
const getCurrentUserId = async () => {
  const { data: { user } } = await supabase.auth.getUser();
  return user?.id;
};

function RemoteInterface() {
  const [state, setState] = useState<RemoteState>({
    selectedHub: null,
    hubMode: 'assigned',
    showScriptNames: false,
    availableScripts: [],
    hubReady: false
  });
  const [showSettings, setShowSettings] = useState(false);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [userId, setUserId] = useState<string | null>(null);
  
  // Get user ID on mount
  useEffect(() => {
    getCurrentUserId().then(setUserId);
  }, []);
  
  // Cleanup subscriptions on unmount
  useEffect(() => {
    return () => {
      subscriptions.forEach(sub => sub.unsubscribe());
    };
  }, [subscriptions]);
  
  // Helper functions
  const requestScriptAssignment = async (hubId: string) => {
    if (!userId) return;
    
    try {
      // Create or update active_remotes entry - this will trigger script assignment
      await supabase.table('active_remotes').upsert({
        hub_id: hubId,
        user_id: userId,
        last_seen: 'now()'
      }, {
        onConflict: 'hub_id,user_id'
      });
      
      // Wait a moment for hub to process the assignment
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Now fetch the assignment
      const { data } = await supabase.table('active_remotes').select('*').eq('hub_id', hubId).eq('user_id', userId).single();
      
      if (data && data.assigned_script) {
        setState(prev => ({
          ...prev,
          assignedScript: data.assigned_script,
          scriptColor: data.script_color
        }));
      }
    } catch (error) {
      console.error('Error requesting script assignment:', error);
    }
  };
  
  const fetchAvailableScripts = async (hubId: string) => {
    try {
      // Get all scripts available on this hub
      const { data } = await supabase.table('hub_scripts').select('script_name').eq('hub_id', hubId);
      return data ? data.map(row => row.script_name) : [];
    } catch (error) {
      console.error('Error fetching scripts:', error);
      return [];
    }
  };
  
  // Connect to hub and check if dependencies are ready
  const connectToHub = async (hubId: string) => {
    try {
      const { data: hubData } = await supabase.from('hubs').select('*').eq('id', hubId).single();
      
      setState(prev => ({
        ...prev,
        selectedHub: hubId,
        hubMode: hubData.mode,
        showScriptNames: hubData.show_script_names,
        hubReady: hubData.dependencies_ready
      }));
      
      if (hubData.dependencies_ready) {
        if (hubData.mode === 'assigned') {
          await requestScriptAssignment(hubId);
        } else {
          const scripts = await fetchAvailableScripts(hubId);
          setState(prev => ({ ...prev, availableScripts: scripts }));
        }
      }
      
      // Subscribe to real-time updates
      subscribeToHubUpdates(hubId);
    } catch (error) {
      console.error('Failed to connect to hub:', error);
    }
  };
  
  const subscribeToHubUpdates = (hubId: string) => {
    const newSubscriptions = [];
    const currentHubMode = state.hubMode; // Capture current mode
    
    try {
      // Subscribe to hub changes (shuffle, dependency updates)
      const hubSub = supabase
        .channel(`hub-updates-${hubId}`)
        .on('postgres_changes', 
          { event: 'UPDATE', schema: 'public', table: 'hubs', filter: `id=eq.${hubId}` },
          (payload) => {
            if (payload.new.dependencies_ready !== payload.old.dependencies_ready) {
              setState(prev => ({ ...prev, hubReady: payload.new.dependencies_ready }));
              
              // Refresh scripts when hub becomes ready
              if (payload.new.dependencies_ready) {
                if (currentHubMode === 'assigned') {
                  requestScriptAssignment(hubId);
                } else {
                  fetchAvailableScripts(hubId).then(scripts => 
                    setState(prev => ({ ...prev, availableScripts: scripts }))
                  );
                }
              }
            }
            
            if (payload.new.last_shuffle !== payload.old.last_shuffle) {
              // Refresh script assignment after shuffle
              if (currentHubMode === 'assigned') {
                requestScriptAssignment(hubId);
              }
            }
          }
        )
        .subscribe();
        
      // Subscribe to active_remotes changes (for assigned mode)
      const remoteSub = supabase
        .channel(`remote-updates-${userId}`)
        .on('postgres_changes',
          { event: '*', schema: 'public', table: 'active_remotes', filter: `user_id=eq.${userId}` },
          (payload) => {
            if (payload.eventType === 'UPDATE' || payload.eventType === 'INSERT') {
              setState(prev => ({
                ...prev,
                assignedScript: payload.new.assigned_script,
                scriptColor: payload.new.script_color
              }));
            }
          }
        )
        .subscribe();
        
      // Subscribe to hub_scripts changes (for shared mode)
      const scriptsSub = supabase
        .channel(`scripts-updates-${hubId}`)
        .on('postgres_changes',
          { event: '*', schema: 'public', table: 'hub_scripts', filter: `hub_id=eq.${hubId}` },
          (payload) => {
            if (currentHubMode === 'shared') {
              fetchAvailableScripts(hubId).then(scripts => 
                setState(prev => ({ ...prev, availableScripts: scripts }))
              );
            }
          }
        )
        .subscribe();
        
      newSubscriptions.push(hubSub, remoteSub, scriptsSub);
      setSubscriptions(prev => [...prev, ...newSubscriptions]);
    } catch (error) {
      console.error('Error setting up subscriptions:', error);
    }
  };
  
  const forceScriptUpdate = async () => {
    if (!state.selectedHub || !userId) return;
    
    try {
      // Disable buttons during update
      setState(prev => ({ ...prev, hubReady: false }));
      
      // Request hub to update scripts
      await supabase.table('hub_commands').insert({
        hub_id: state.selectedHub,
        action: 'update_scripts',
        requested_by: userId
      });
      
      // Real-time subscription will handle re-enabling when ready
    } catch (error) {
      console.error('Error requesting script update:', error);
    }
  };
  
  if (!userId) {
    return <div>Please log in to use the remote</div>;
  }
  
  return (
    <div className="remote-interface">
      {!state.selectedHub ? (
        <HubSelector onHubSelect={connectToHub} />
      ) : (
        <>
          {!state.hubReady && (
            <div className="loading-message">
              Hub is installing dependencies... Please wait.
            </div>
          )}
          
          <div className="button-area">
            {state.hubReady ? (
              state.hubMode === 'assigned' ? (
                <SinglePressButton {...state} userId={userId} />
              ) : (
                <MultipleButtons scripts={state.availableScripts} hubId={state.selectedHub} showScriptNames={state.showScriptNames} userId={userId} />
              )
            ) : (
              <div className="buttons-disabled">Buttons disabled until dependencies ready</div>
            )}
          </div>
          
          <div className="controls">
            <button onClick={forceScriptUpdate} disabled={!state.hubReady}>
              🔄 Update Scripts
            </button>
            
            <button 
              className="settings-toggle"
              onClick={() => setShowSettings(!showSettings)}
            >
              ⚙️
            </button>
          </div>
          
          {showSettings && (
            <SettingsPanel 
              hubId={state.selectedHub} 
              onClose={() => setShowSettings(false)} 
            />
          )}
        </>
      )}
    </div>
  );
}
```

### Hub Selector & Button Components

```typescript
function HubSelector({ onHubSelect }: { onHubSelect: (hubId: string) => void }) {
  const [hubs, setHubs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchHubs = async () => {
      try {
        const { data } = await supabase
          .from('hubs')
          .select('*')
          .eq('status', 'online');
        setHubs(data || []);
      } catch (error) {
        console.error('Error fetching hubs:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchHubs();
  }, []);
  
  if (loading) {
    return <div>Loading hubs...</div>;
  }
  
  if (hubs.length === 0) {
    return <div>No online hubs available</div>;
  }
  
  return (
    <div className="hub-selector">
      <h2>Select Hub</h2>
      {hubs.map(hub => (
        <button 
          key={hub.id}
          onClick={() => onHubSelect(hub.id)}
          className="hub-button"
        >
          {hub.friendly_name} ({hub.mode} mode)
        </button>
      ))}
    </div>
  );
}

function SinglePressButton({ assignedScript, scriptColor, showScriptNames, selectedHub, userId }: RemoteState & { userId: string }) {
  const [isExecuting, setIsExecuting] = useState(false);
  
  const executeScript = async () => {
    if (!assignedScript || !selectedHub) return;
    
    setIsExecuting(true);
    
    try {
      await supabase.table('script_commands').insert({
        hub_id: selectedHub,
        user_id: userId,
        script_name: assignedScript,
        status: 'pending'
      });
      
      // Update last_seen for this remote
      await supabase.table('active_remotes').update({
        last_seen: 'now()'
      }).eq('hub_id', selectedHub).eq('user_id', userId);
    } catch (error) {
      console.error('Error executing script:', error);
    } finally {
      setIsExecuting(false);
    }
  };
  
  if (!assignedScript) {
    return <div>Waiting for script assignment...</div>;
  }
  
  return (
    <button 
      className="press-button single"
      style={{ backgroundColor: scriptColor }}
      onClick={executeScript}
      disabled={isExecuting}
    >
      <div className="button-label">PRESS</div>
      {showScriptNames && (
        <div className="script-name">{assignedScript}</div>
      )}
    </button>
  );
}

function MultipleButtons({ scripts, hubId, showScriptNames, userId }: { scripts: string[], hubId: string, showScriptNames: boolean, userId: string }) {
  const executeScript = async (scriptName: string) => {
    try {
      await supabase.table('script_commands').insert({
        hub_id: hubId,
        user_id: userId,
        script_name: scriptName,
        status: 'pending'
      });
    } catch (error) {
      console.error('Error executing script:', error);
    }
  };
  
  if (scripts.length === 0) {
    return <div>No scripts available on this hub</div>;
  }
  
  return (
    <div className="multiple-buttons">
      {scripts.map((script, index) => (
        <button
          key={script}
          className="press-button multiple"
          style={{ backgroundColor: `hsl(${(index * 137.5) % 360}, 70%, 50%)` }}
          onClick={() => executeScript(script)}
        >
          <div className="button-label">PRESS</div>
          <div className="script-name">{script}</div>
        </button>
      ))}
    </div>
  );
}

function SettingsPanel({ hubId, onClose }: { hubId: string, onClose: () => void }) {
  const [settings, setSettings] = useState({
    showScriptNames: false,
    autoShuffleEnabled: false,
    autoShuffleInterval: 300
  });
  const [shuffleCountdown, setShuffleCountdown] = useState(0);
  
  useEffect(() => {
    // Load current settings
    const loadSettings = async () => {
      try {
        const { data } = await supabase.from('hubs').select('*').eq('id', hubId).single();
        if (data) {
          setSettings({
            showScriptNames: data.show_script_names,
            autoShuffleEnabled: data.auto_shuffle_enabled,
            autoShuffleInterval: data.auto_shuffle_interval
          });
        }
      } catch (error) {
        console.error('Error loading settings:', error);
      }
    };
    
    loadSettings();
    
    // Subscribe to shuffle countdown updates
    const subscription = supabase
      .channel(`settings-updates-${hubId}`)
      .on('postgres_changes', 
        { event: 'UPDATE', schema: 'public', table: 'hubs', filter: `id=eq.${hubId}` },
        (payload) => {
          if (payload.new.shuffle_countdown !== undefined) {
            setShuffleCountdown(payload.new.shuffle_countdown);
          }
        }
      )
      .subscribe();
      
    return () => subscription.unsubscribe();
  }, [hubId]);
  
  const updateHubSettings = async (newSettings: Partial<typeof settings>) => {
    try {
      await supabase.table('hubs').update(newSettings).eq('id', hubId);
      setSettings(prev => ({ ...prev, ...newSettings }));
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };
  
  const manualShuffle = async () => {
    try {
      // Trigger immediate shuffle
      await supabase.table('hubs').update({ 
        last_shuffle: new Date().toISOString() 
      }).eq('id', hubId);
    } catch (error) {
      console.error('Error triggering shuffle:', error);
    }
  };
  
  return (
    <div className="settings-panel">
      <h3>Hub Settings</h3>
      
      <label>
        <input 
          type="checkbox"
          checked={settings.showScriptNames}
          onChange={(e) => updateHubSettings({ show_script_names: e.target.checked })}
        />
        Show Script Names
      </label>
      
      <label>
        <input 
          type="checkbox"
          checked={settings.autoShuffleEnabled}
          onChange={(e) => updateHubSettings({ auto_shuffle_enabled: e.target.checked })}
        />
        Auto-Shuffle Enabled
      </label>
      
      {settings.autoShuffleEnabled && (
        <>
          <label>
            Shuffle Interval (seconds):
            <input 
              type="number"
              value={settings.autoShuffleInterval}
              onChange={(e) => updateHubSettings({ auto_shuffle_interval: parseInt(e.target.value) })}
            />
          </label>
          
          {shuffleCountdown > 0 && (
            <div className="countdown">
              Next shuffle in: {shuffleCountdown}s
            </div>
          )}
        </>
      )}
      
      <button onClick={manualShuffle}>Shuffle Now</button>
      <button onClick={onClose}>Close</button>
    </div>
  );
}

export default RemoteInterface;
```

### Settings Panel

```typescript
function SettingsPanel({ hubId, onClose }: { hubId: string, onClose: () => void }) {
  const [settings, setSettings] = useState({
    showScriptNames: false,
    autoShuffleEnabled: false,
    autoShuffleInterval: 300
  });
  
  const updateHubSettings = async (newSettings: Partial<typeof settings>) => {
    await supabase.table('hubs').update(newSettings).eq('id', hubId);
    setSettings(prev => ({ ...prev, ...newSettings }));
  };
  
  const manualShuffle = async () => {
    // Trigger shuffle by updating a timestamp field
    await supabase.table('hubs').update({ 
      last_shuffle: new Date().toISOString() 
    }).eq('id', hubId);
  };
  
  return (
    <div className="settings-panel">
      <h3>Hub Settings</h3>
      
      <label>
        <input 
          type="checkbox"
          checked={settings.showScriptNames}
          onChange={(e) => updateHubSettings({ showScriptNames: e.target.checked })}
        />
        Show Script Names
      </label>
      
      <label>
        <input 
          type="checkbox"
          checked={settings.autoShuffleEnabled}
          onChange={(e) => updateHubSettings({ autoShuffleEnabled: e.target.checked })}
        />
        Auto-Shuffle Enabled
      </label>
      
      {settings.autoShuffleEnabled && (
        <label>
          Shuffle Interval (seconds):
          <input 
            type="number"
            value={settings.autoShuffleInterval}
            onChange={(e) => updateHubSettings({ autoShuffleInterval: parseInt(e.target.value) })}
          />
        </label>
      )}
      
      <button onClick={manualShuffle}>Shuffle Now</button>
      <button onClick={onClose}>Close</button>
    </div>
  );
}
```

## Real-time Communication

### Hub Listening for Commands

```python
def listen_for_commands(self):
    """Subscribe to script commands via Supabase real-time"""
    
    def handle_command(payload):
        command_data = payload['new']
        if command_data['hub_id'] == self.hub_id and command_data['status'] == 'pending':
            self.execute_script(command_data)
    
    # Subscribe to script_commands table
    self.supabase.table('script_commands').on('INSERT', handle_command).subscribe()
    
def execute_script(self, command_data):
    """Execute the requested script using UV in the script's directory"""
    script_folder = command_data['script_name']  # This is the folder name
    command_id = command_data['id']
    
    try:
        # Update status to executing
        self.supabase.table('script_commands').update({
            'status': 'executing'
        }).eq('id', command_id).execute()
        
        # Execute with UV - will auto-install deps on first run, cache afterward
        result = self.execute_script_with_uv(script_folder)
        
        # Record result
        self.supabase.table('script_results').insert({
            'command_id': command_id,
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }).execute()
        
        # Update command status
        self.supabase.table('script_commands').update({
            'status': 'completed'
        }).eq('id', command_id).execute()
        
        # Update usage count (fix increment logic)
        existing_usage = self.supabase.table('script_usage').select('usage_count').eq('hub_id', self.hub_id).eq('script_name', script_folder).execute()
        
        if existing_usage.data:
            new_count = existing_usage.data[0]['usage_count'] + 1
        else:
            new_count = 1
        
        self.supabase.table('script_usage').upsert({
            'hub_id': self.hub_id,
            'script_name': script_folder,
            'usage_count': new_count,
            'last_used': 'now()'
        }, on_conflict='hub_id,script_name').execute()
        
    except Exception as e:
        # Handle execution errors
        self.supabase.table('script_results').insert({
            'command_id': command_id,
            'exit_code': -1,
            'stderr': str(e),
            'success': False
        }).execute()
        
        self.supabase.table('script_commands').update({
            'status': 'failed'
        }).eq('id', command_id).execute()
```

## Key Features

### Modes
- **Shared Mode**: All remotes see all available scripts as buttons
- **Assigned Mode**: Each remote gets one randomly assigned script button

### Fair Distribution
- Tracks usage count per script per hub
- Always assigns least-used scripts first
- Prevents script monopolization

### Settings Panel
- Toggle script name visibility
- Enable/disable auto-shuffle timer
- Manual shuffle button
- Shared across all remotes on the same hub

### Real-time Updates
- Script assignment changes propagate immediately
- Command execution status updates
- Hub online/offline status

## Next Steps
1. Implement shuffle functionality (manual + auto-timer)
2. Add settings panel to remote frontend
3. Handle hub disconnection/reconnection
4. Add error handling and retry logic
5. Implement script result display in remote UI