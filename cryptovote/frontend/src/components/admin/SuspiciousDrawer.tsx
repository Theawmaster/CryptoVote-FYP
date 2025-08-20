import { Bell } from 'lucide-react';
import type { Suspicious } from '../../services/admin/types';

export function SecurityBell({
  count, onClick,
}: { count: number; onClick: () => void }) {
  return (
    <button className="mgr-icon-btn" onClick={onClick} aria-label="Security notifications" title="Security notifications">
      <Bell className="w-6 h-6"/>
      {count > 0 && <span className="mgr-badge-dot">{count}</span>}
    </button>
  );
}

export function SuspiciousDrawer({
  open, onClose, items, loading, onRefresh, onExportCsv, onExportPdf,
}: {
  open: boolean; onClose: () => void;
  items: Suspicious[]; loading: boolean;
  onRefresh: () => void; onExportCsv: () => void; onExportPdf: () => void;
}) {
  if (!open) return null;
  return (
    <div className="mgr-drawer-backdrop" onClick={onClose}>
      <aside className="mgr-drawer" onClick={e => e.stopPropagation()}>
        <div className="mgr-drawer-head">
          <h3>Suspicious Activity</h3>
          <div className="flex gap-2">
            <button className="mgr-link" onClick={onRefresh} title="Refresh">↺</button>
            <button className="mgr-link" onClick={onExportCsv} title="Export CSV">Export CSV</button>
            <button className="mgr-link" onClick={onExportPdf} title="Export PDF">Export PDF</button>
            <button className="mgr-link" onClick={onClose}>X</button>
          </div>
        </div>

        {loading ? (
          <div className="mgr-list-empty">Loading…</div>
        ) : items.length === 0 ? (
          <div className="mgr-list-empty">No suspicious activity 🎉</div>
        ) : (
          <div className="mgr-list">
            {items.map(it => (
              <div key={it.id} className="mgr-card">
                <div className="mgr-card-top"><span className="mgr-chip">Alert</span></div>
                <div className="mgr-card-title">{it.reason}</div>
                <div className="mgr-card-meta">
                  {(it.email ?? 'anon')} • {it.ip_address} • {it.timestamp ? new Date(it.timestamp).toLocaleString() : '—'}
                </div>
                <div className="mgr-card-route">{it.route_accessed}</div>
              </div>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}
