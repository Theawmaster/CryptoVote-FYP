export type Election = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  tally_generated: boolean;
};

export type AdminMe = {
  last_login_at?: string | null;
  last_login_ip?: string | null;
  last_2fa_at?: string | null;
  role?: string | null;
};

export type Suspicious = {
  id: number;
  email: string | null;
  ip_address: string;
  reason: string;
  route_accessed: string;
  timestamp: string | null;
};

export type ElectionStatus = {
  id: string;
  name: string;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  start_time: string | null;
  end_time: string | null;
  tally_generated: boolean;
  candidate_count?: number;
  vote_count?: number;
};

export type ModalKind = 'start' | 'end' | 'tally' | 'report';
