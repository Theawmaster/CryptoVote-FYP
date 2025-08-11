import React, { useEffect, useRef, useState, useMemo } from 'react';
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

const AdminLandingPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email as string | undefined;

  const [elections, setElections] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('all');
  const [showCreate, setShowCreate] = useState(false);            

  const fetchAbortRef = useRef<AbortController | null>(null);

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

  const filtered = useMemo(() => {
    switch (filter) {
      case 'active':   return elections.filter(e => e.is_active);
      case 'ended':    return elections.filter(e => e.has_ended);
      case 'upcoming': return elections.filter(e => !e.has_started);
      default:         return elections;
    }
  }, [elections, filter]);

  return (
    <div className="admin-landing">
      <LeftSidebar title="Admin Landing Page" />

      <main className="right-panel">
        <h2>Your Voting Campaigns</h2>

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
                    {e.start_time
                      ? `Starts: ${new Date(e.start_time).toLocaleString()}`
                      : 'Starts: —'}
                    <br />
                    {e.end_time
                      ? `Ends: ${new Date(e.end_time).toLocaleString()}`
                      : 'Ends: —'}
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
        
      </main>
    </div>
  );
};

export default AdminLandingPage;
