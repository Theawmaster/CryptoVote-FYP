export type Election = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  candidate_count: number;
};

export type VoterMe = {
  last_login_at?: string | null;
  last_login_ip?: string | null;
  last_2fa_at?: string | null;
  role?: string | null;
};