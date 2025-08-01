export interface ScriptCommand {
  id: string;
  hub_id: string;
  user_id: string;
  script_name: string;
  status: 'pending' | 'executing' | 'completed' | 'failed';
  created_at: string;
}

export interface ScriptResult {
  id: string;
  command_id: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  success: boolean;
  result: {
    success: boolean;
    output: string;
    error?: string;
    duration_ms: number;
    script_name: string;
    timestamp: string;
  };
}

export interface FriendlyName {
  script_name: string;
  friendly_name: string;
  updated_at: string;
}