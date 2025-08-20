export function fmtAbs(iso?: string | null, tz = 'Asia/Singapore') {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en-SG', {
    timeZone: tz, year: 'numeric', month: 'short', day: '2-digit',
    hour: 'numeric', minute: '2-digit', hour12: true,
  }).format(new Date(iso));
}

export function fmtRel(iso?: string | null) {
  if (!iso) return 'first login';
  const t = new Date(iso).getTime();
  const mins = Math.max(0, Math.round((Date.now() - t) / 60000));
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}
