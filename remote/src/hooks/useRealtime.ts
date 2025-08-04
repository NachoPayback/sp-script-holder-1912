import { useEffect, useRef, useState } from 'react';
import { supabase } from '../services/supabase';
import type { RealtimeChannel } from '@supabase/supabase-js';

export const useRealtime = (hubId: string) => {
  const channelRef = useRef<RealtimeChannel | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [scriptCommands, setScriptCommands] = useState<any[]>([]);

  useEffect(() => {
    if (!hubId || hubId === '') {
      console.log('useRealtime: No hubId provided');
      return;
    }

    console.log('useRealtime: Setting up channel for hubId:', hubId);

    // Create real-time channel with unique name
    const channelName = `script-commands-${hubId}`;
    const channel = supabase.channel(channelName);
    channelRef.current = channel;

    // Handle script command events
    const handleCommand = (payload: any) => {
      console.log('Real-time event received:', payload.eventType, payload);
      const command = payload.new as any;
      
      if (command && command.id) {
        setScriptCommands(prev => {
          const existingIndex = prev.findIndex(cmd => cmd.id === command.id);
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = command;
            console.log('Updated existing command:', command.id, 'status:', command.status);
            return updated;
          } else {
            console.log('Added new command:', command.id, 'status:', command.status);
            return [command, ...prev.slice(0, 49)];
          }
        });
      }
    };

    // Listen for both INSERT and UPDATE events
    channel
      .on(
        'postgres_changes',
        {
          event: '*', // Listen to all events
          schema: 'public',
          table: 'script_commands',
          filter: `hub_id=eq.${hubId}`
        },
        handleCommand
      )
      .subscribe((status) => {
        console.log('Real-time subscription status:', status);
        setIsConnected(status === 'SUBSCRIBED');
        
        if (status === 'SUBSCRIBED') {
          console.log('Successfully subscribed to script commands for hub:', hubId);
        } else if (status === 'CLOSED') {
          console.log('Real-time subscription closed');
        }
      });

    return () => {
      console.log('Cleaning up real-time subscription');
      if (channelRef.current) {
        channelRef.current.unsubscribe();
      }
      setIsConnected(false);
    };
  }, [hubId]);

  return {
    isConnected,
    scriptCommands
  };
};