import { useEffect, useState } from 'react';
import { supabase } from '../services/supabase';
import type { Hub } from '../types/Hub';

export const useHubPresence = (enabled: boolean) => {
  const [hubs, setHubs] = useState<Hub[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!enabled) return;

    console.log('Setting up hub presence subscription...');
    const channel = supabase.channel('hub-presence')
      .on('presence', { event: 'sync' }, () => {
        const state = channel.presenceState();
        console.log('Hub presence sync:', state);
        
        // Convert presence state to hub format
        const presenceHubs = Object.entries(state).map(([, presences]: [string, any]) => {
          const presence = Array.isArray(presences) ? presences[0] : presences;
          return {
            id: presence.hub_id,
            machine_id: presence.machine_id,
            friendly_name: presence.friendly_name,
            status: 'online' as const,
            scripts: presence.scripts || [],
            script_count: presence.script_count || 0,
            mode: 'shared' as const,
            show_script_names: false,
            last_heartbeat: new Date().toISOString(),
            auto_shuffle_enabled: false,
            auto_shuffle_interval: 300
          } as Hub;
        });
        
        setHubs(presenceHubs);
      })
      .on('presence', { event: 'join' }, ({ key, newPresences }) => {
        console.log('Hub joined:', key, newPresences);
      })
      .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
        console.log('Hub left:', key, leftPresences);
      })
      .subscribe((status) => {
        console.log('Hub presence subscription status:', status);
        setIsConnected(status === 'SUBSCRIBED');
      });

    return () => {
      console.log('Cleaning up hub presence subscription');
      channel.unsubscribe();
      setIsConnected(false);
    };
  }, [enabled]);

  return { hubs, isConnected };
};