import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Bell } from 'lucide-react';
import LeftSidebar from '../../components/ui/AdminLeftSideBar';
import CreateElectionForm from '../../components/form/CreateElectionForm';
import { useLocation, useNavigate } from 'react-router-dom';
import '../../styles/admin-landing.css';

type Election = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  tally_generated: boolean;
};
type FilterKey = 'all' | 'active' | 'ended' | 'upcoming';
type Suspicious = {
  id: number;
  email: string | null;
  ip_address: string;
  reason: string;
  route_accessed: string;
  timestamp: string | null;
};

// ADDED: minimal shape for /admin/me
type AdminMe = {
  last_login_at?: string | null;
  last_login_ip?: string | null;
  last_2fa_at?: string | null;
  role?: string | null;
};

const AdminLandingPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email as string | undefined;

  const [elections, setElections] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('all');
  const [showCreate, setShowCreate] = useState(false);

  // Suspicious activity state
  const [secOpen, setSecOpen] = useState(false);
  const [secCount, setSecCount] = useState(0);
  const [secItems, setSecItems] = useState<Suspicious[]>([]);
  const [secLoading, setSecLoading] = useState(false);
  const [exportErr, setExportErr] = useState<string | null>(null);

  const fetchAbortRef = useRef<AbortController | null>(null);

  // ADDED: /admin/me state
  const [me, setMe] = useState<AdminMe | null>(null);
  // ADDED: tick every 60s so relative time refreshes without reload
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 60000);
    return () => clearInterval(id);
  }, []);

  // Elections fetch
  useEffect(() => {
    const controller = new AbortController();
    fetchAbortRef.current = controller;

    (async () => {
      try {
        setLoading(true);
        setErr(null);

        const res = await fetch('/admin/elections', {
          credentials: 'include',
          signal: controller.signal,
        });

        if (res.status === 403) {
          setElections([]);
          setErr('Your session has expired. Please log in again.');
          return;
        }

        const ct = res.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
          const txt = await res.text();
          console.warn('Non-JSON /admin/elections', res.status, txt.slice(0, 200));
          setErr(`Server returned ${res.status}.`);
          return;
        }

        const data = await res.json();
        if (!res.ok) throw new Error(data?.error || 'Failed to load elections');

        setElections(data.elections || []);
      } catch (e: any) {
        if (e.name !== 'AbortError') setErr(e.message || 'Failed to load elections');
      } finally {
        setLoading(false);
      }
    })();

    return () => controller.abort();
  }, []);

  // ADDED: fetch /admin/me once
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/admin/me', { credentials: 'include' });
        if (!r.ok) return; // ignore if not admin / no session
        const d: AdminMe = await r.json();
        setMe(d);
      } catch {
        /* ignore */
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    switch (filter) {
      case 'active':   return elections.filter(e => e.is_active);
      case 'ended':    return elections.filter(e => e.has_ended);
      case 'upcoming': return elections.filter(e => !e.has_started);
      default:         return elections;
    }
  }, [elections, filter]);

  // Suspicious: count + list
  async function refreshSecCount() {
    try {
      const r = await fetch('/admin/security/suspicious/count', { credentials: 'include' });
      if (!r.ok) return;
      const d = await r.json();
      setSecCount(d.count ?? 0);
    } catch {
      /* ok to ignore */
    }
  }

  async function loadSuspicious() {
    setSecLoading(true);
    try {
      const r = await fetch('/admin/security/suspicious?limit=50', { credentials: 'include' });
      const d = await r.json();
      setSecItems(d.items ?? []);
    } catch {
      setSecItems([]);
    }
    setSecLoading(false);
  }

  useEffect(() => {
    refreshSecCount();
    const id = setInterval(refreshSecCount, 15000);
    return () => clearInterval(id);
  }, []);

  // ---- File export helpers (CSV/PDF via blob) ----
  function triggerDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function exportCsv() {
    setExportErr(null);
    try {
      const res = await fetch('/admin/security/suspicious.csv', {
        credentials: 'include',
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try { msg = (await res.json())?.error || msg; } catch {}
        throw new Error(msg);
      }
      const blob = await res.blob();
      const ct = res.headers.get('content-type') || '';
      if (!ct.includes('text/csv')) {
        console.warn('Unexpected content-type for CSV:', ct);
      }
      triggerDownload(blob, 'suspicious.csv');
    } catch (e: any) {
      setExportErr(e.message || 'Failed to download CSV');
    }
  }

  async function exportPdf() {
    setExportErr(null);
    try {
      const res = await fetch('/admin/security/suspicious.pdf', {
        credentials: 'include',
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try { msg = (await res.json())?.error || msg; } catch {}
        throw new Error(msg);
      }
      const blob = await res.blob();
      triggerDownload(blob, 'suspicious.pdf');
    } catch (e: any) {
      setExportErr(e.message || 'Failed to download PDF');
    }
  }

  // ADDED: formatting helpers for last login
  function fmtAbs(iso?: string | null, tz = 'Asia/Singapore') {
    if (!iso) return '—';
    return new Intl.DateTimeFormat('en-SG', {
      timeZone: tz,
      year: 'numeric', month: 'short', day: '2-digit',
      hour: 'numeric', minute: '2-digit', hour12: true,
    }).format(new Date(iso));
  }
  function fmtRel(iso?: string | null) {
    if (!iso) return 'first login';
    const t = new Date(iso).getTime();
    const mins = Math.max(0, Math.round((Date.now() - t) / 60000));
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const h = Math.round(mins / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.round(h / 24)}d ago`;
  }

  return (
    <div className="admin-landing">
      <LeftSidebar title="Admin Landing Page" />

      <main className="right-panel">
        {/* header row with bell + ADDED: last login chip */}
        <div className="mgr-header-row">
          <h2>Your Voting Campaigns</h2>

          <div className="flex items-center gap-3">
            {me && (
              <span
                className="mgr-lastlogin-chip"
                title={`Last login: ${fmtAbs(me.last_login_at)} (Asia/Singapore)` +
                  (me.last_login_ip ? ` • IP: ${me.last_login_ip}` : '')}
                aria-label="Last login"
              >
                {/* tiny clock icon */}
                <svg width="16" height="16" viewBox="0 0 24 24" style={{ opacity: 0.8 }}>
                  <path fill="currentColor" d="M12 1a11 11 0 1 0 11 11A11.012 11.012 0 0 0 12 1Zm1 11.59V7h-2v6h6v-2Z"/>
                </svg>
                <span className="mgr-chip-label">Last login</span>
                <span>• {fmtAbs(me.last_login_at)} (SGT)</span>
                <span className="mgr-chip-muted">• {fmtRel(me.last_login_at)}</span>
              </span>
            )}

            <button
              className="mgr-icon-btn"
              onClick={() => { setSecOpen(true); loadSuspicious(); }}
              aria-label="Security notifications"
              title="Security notifications"
            >
              <Bell className="w-6 h-6" />
              {secCount > 0 && <span className="mgr-badge-dot">{secCount}</span>}
            </button>
          </div>
        </div>

        <div className="filter-bar">
          {(['all','active','ended','upcoming'] as FilterKey[]).map(key => (
            <button
              key={key}
              className={`filter-pill ${filter === key ? 'active' : ''}`}
              onClick={() => setFilter(key)}
            >
              {key[0].toUpperCase() + key.slice(1)}
            </button>
          ))}
        </div>

        {loading && (
          <div className="skeleton-grid">
            {[...Array(3)].map((_,i)=><div key={i} className="skeleton-card" />)}
          </div>
        )}

        {err && <div style={{ color: 'crimson' }}>{err}</div>}

        {!loading && !err && (
          <>
            <div className="elections-grid">
              {filtered.map((e) => (
                <div key={e.id} className="election-card">
                  <div className="title">{e.name}</div>
                  <div className="meta">
                    ID: {e.id}<br />
                    {e.start_time ? `Starts: ${new Date(e.start_time).toLocaleString()}` : 'Starts: —'}
                    <br />
                    {e.end_time ? `Ends: ${new Date(e.end_time).toLocaleString()}` : 'Ends: —'}
                  </div>
                  <div>
                    {e.is_active && <span className="badge">Active</span>}
                    {e.has_ended && <span className="badge">Ended</span>}
                    {!e.has_started && <span className="badge">Not started</span>}
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <button
                      className="auth-submit"
                      onClick={() => navigate(`/admin/manage/${e.id}`, { state: { email } })}
                    >
                      More
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Create New below the grid */}
            <div
              className="create-section"
              onClick={() => {
                setShowCreate(true);
                setTimeout(() =>
                  document.getElementById('create-election-anchor')
                    ?.scrollIntoView({ behavior: 'smooth' }), 0);
              }}
            >
              <div className="create-card">+ Create new</div>
            </div>

            {showCreate && (
              <CreateElectionForm
                onCreated={(e) => {
                  setElections(prev => [e, ...prev]);
                  setShowCreate(false);
                }}
              />
            )}
          </>
        )}

        {/* ===== Suspicious Activity Drawer ===== */}
        {secOpen && (
          <div className="mgr-drawer-backdrop" onClick={() => setSecOpen(false)}>
            <aside className="mgr-drawer" onClick={(e) => e.stopPropagation()}>
              <div className="mgr-drawer-head">
                <h3>Suspicious Activity</h3>
                <div className="flex gap-2">
                  <button className="mgr-link" onClick={() => loadSuspicious()} title="Refresh">
                    ↺
                  </button>
                  <button className="mgr-link" onClick={exportCsv} title="Export CSV">
                    Export CSV
                  </button>
                  <button className="mgr-link" onClick={exportPdf} title="Export PDF">
                    Export PDF
                  </button>
                  <button className="mgr-link" onClick={() => setSecOpen(false)}>
                    X
                  </button>
                </div>
              </div>

              {exportErr && <div style={{ color:'crimson', marginBottom:8 }}>{exportErr}</div>}

              {secLoading ? (
                <div className="mgr-list-empty">Loading…</div>
              ) : secItems.length === 0 ? (
                <div className="mgr-list-empty">No suspicious activity 🎉</div>
              ) : (
                <div className="mgr-list">
                  {secItems.map(it => (
                    <div key={it.id} className="mgr-card">
                      <div className="mgr-card-top">
                        <span className="mgr-chip">Alert</span>
                      </div>
                      <div className="mgr-card-title">{it.reason}</div>
                      <div className="mgr-card-meta">
                        {(it.email ?? 'anon')} • {it.ip_address} •{' '}
                        {it.timestamp ? new Date(it.timestamp).toLocaleString() : '—'}
                      </div>
                      <div className="mgr-card-route">{it.route_accessed}</div>
                    </div>
                  ))}
                </div>
              )}
            </aside>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminLandingPage;
