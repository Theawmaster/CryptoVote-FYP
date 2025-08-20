import type { ElectionStatus } from '../services/admin/types';

export const fmtTime = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleString() : '—';

export function prettyState(s?: ElectionStatus | null) {
  if (!s) return '';
  if (s.has_ended) return 'Ended';
  if (s.is_active) return 'Active';
  if (s.has_started) return 'Running';
  return 'Not started';
}
