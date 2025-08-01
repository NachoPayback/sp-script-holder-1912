import { useEffect, useRef, useState } from 'react';
import { supabase } from '../services/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';

export const useRealtime = (hubId: string) => {
  const channelRef = useRef<RealtimeChannel | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [scriptCommands, setScriptCommands] = useState<{ id: string; command_id: string; status: string; result?: string }[]>([]);

  useEffect(() => {
    if (!hubId || hubId === '') return;

    // Create real-time channel
    const channel = supabase.channel(`hub-${hubId}`);
    channelRef.current = channel;

    // Listen for script command status updates
    channel.on(
      'postgres_changes',
      {
        event: 'UPDATE',
        schema: 'public',
        table: 'script_commands',
        filter: `hub_id=eq.${hubId}`
      },
      (payload) => {
        const command = payload.new as { id: string; command_id: string; status: string; result?: string };
        setScriptCommands(prev => [command, ...prev.slice(0, 49)]);
      }
    );

    // Subscribe to the channel
    channel.subscribe((status) => {
      setIsConnected(status === 'SUBSCRIBED');
    });

    return () => {
      channel.unsubscribe();
      setIsConnected(false);
    };
  }, [hubId]);

  return {
    isConnected,
    scriptCommands
  };
};