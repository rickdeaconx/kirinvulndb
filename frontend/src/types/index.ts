export interface Vulnerability {
  id: string;
  vulnerability_id: string;
  cve_id?: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  cvss_score?: number;
  cvss_vector?: string;
  discovery_date?: string;
  public_disclosure?: string;
  attack_vectors: AttackVector[];
  patch_status: 'unpatched' | 'patch_available' | 'patched' | 'wont_fix';
  affected_versions?: Record<string, string[]>;
  fixed_versions?: Record<string, string[]>;
  poc_available: boolean;
  exploit_in_wild: boolean;
  tags: string[];
  references: string[];
  affected_tools: string[];
  kirin_remediation_available: boolean;
  created_at: string;
  updated_at: string;
}

export type AttackVector = 
  | 'rce'
  | 'xss'
  | 'injection'
  | 'privilege_escalation'
  | 'prompt_injection'
  | 'data_exfiltration'
  | 'model_poisoning'
  | 'backdoor';

export interface AITool {
  id: string;
  name: string;
  display_name: string;
  vendor: string;
  description?: string;
  current_version?: string;
  supported_languages?: string[];
  platform_support?: string[];
  is_actively_monitored: boolean;
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
  created_at: string;
  updated_at: string;
}

export interface Alert {
  id: string;
  vulnerability_id: string;
  alert_type: 'new_vulnerability' | 'severity_upgrade' | 'exploit_available' | 'patch_available' | 'mass_exploitation' | 'zero_day';
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'pending' | 'sent' | 'acknowledged' | 'resolved' | 'suppressed';
  title: string;
  message: string;
  summary?: string;
  scheduled_time?: string;
  sent_time?: string;
  acknowledged_time?: string;
  is_automated: boolean;
  created_at: string;
  updated_at: string;
}

export interface VulnerabilityStats {
  period_days: number;
  total_vulnerabilities: number;
  recent_vulnerabilities: number;
  severity_distribution: Record<string, number>;
  patch_status_distribution: Record<string, number>;
  tool_distribution: Record<string, number>;
  generated_at: string;
}

export interface AlertStats {
  period_days: number;
  total_alerts: number;
  priority_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  type_distribution: Record<string, number>;
  generated_at: string;
}

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data?: any;
}

export interface PaginatedResponse<T> {
  items?: T[];
  vulnerabilities?: T[];
  tools?: T[];
  alerts?: T[];
  total: number;
  limit: number;
  offset: number;
}