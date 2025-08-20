import type { Election } from '../../services/admin/types';

export default function ElectionCard({
  e, onMore,
}: { e: Election; onMore: (id: string) => void }) {
  return (
    <div className="election-card">
      <div className="title">{e.name}</div>
      <div className="meta">
        ID: {e.id}<br/>
        {e.start_time ? `Starts: ${new Date(e.start_time).toLocaleString()}` : 'Starts: —'}<br/>
        {e.end_time ? `Ends: ${new Date(e.end_time).toLocaleString()}` : 'Ends: —'}
      </div>
      <div>
        {e.is_active && <span className="badge">Active</span>}
        {e.has_ended && <span className="badge">Ended</span>}
        {!e.has_started && <span className="badge">Not started</span>}
      </div>
      <div style={{ marginTop: 12 }}>
        <button className="auth-submit" onClick={() => onMore(e.id)}>More</button>
      </div>
    </div>
  );
}
