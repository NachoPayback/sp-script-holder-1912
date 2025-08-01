export interface Hub {
  id: string;
  machine_id: string;
  friendly_name: string;
  mode: 'shared' | 'assigned';
  show_script_names: boolean;
  auto_shuffle_enabled: boolean;
  auto_shuffle_interval: number;
  status: 'online' | 'offline';
  script_count: number;
  last_seen?: string;
  created_at?: string;
}

export interface HubScript {
  id: string;
  hub_id: string;
  script_name: string;
  friendly_name: string;
  created_at?: string;
}

export interface Assignment {
  hub_id: string;
  user_id: string;
  assigned_script: string;
  script_color: string;
  last_seen: string;
}