
import { getJSON, postJSON } from './http';

export type Election = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  candidate_count: number;
  rsa_key_id?: string;
};

export async function fetchActiveElections() {
  return getJSON<{ elections: Election[] }>('/voter/elections/active');
}

export async function fetchElectionDetail(electionId: string) {
  return getJSON<Election & { candidates?: Array<{id:string; name:string}> }>(`/voter/elections/${electionId}`);
}

export async function blindSign(electionId: string, payload: { blinded_token_hex: string; rsa_key_id?: string; }) {
  return postJSON<{ signed_blinded_token_hex?: string; signed_blinded_token?: string; signed?: string }>(
    `/elections/${electionId}/blind-sign`,
    payload
  );
}

export async function fetchResults(electionId: string) {
  return getJSON<any>(`/results/${encodeURIComponent(electionId)}`);
}

export type Candidate = { id: string; name: string };
export type ElectionDetail = {
  id: string; name: string; rsa_key_id?: string; candidates: Candidate[];
};

export async function fetchElectionDetailBallot(electionId: string) {
  return getJSON<ElectionDetail>(`/voter/elections/${electionId}`);
}