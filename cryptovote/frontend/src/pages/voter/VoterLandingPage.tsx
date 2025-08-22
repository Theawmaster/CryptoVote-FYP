import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/voter-landing.css';
import { useEnsureVoter } from '../../hooks/useAuthGuard';
import LastLoginBadge from '../../components/voter/LastLoginBadge';
import VoterRightSidebar from '../../components/voter/VoterRightSidebar';

type Election = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  candidate_count: number;
};

function useVoterMe() {
  const [me, setMe] = useState<any>(null);
  useEffect(() => {
    fetch('/whoami', { credentials: 'include' })
      .then(r => r.json())
      .then(setMe)
      .catch(() => setMe(null));
  }, []);
  return me;
}

const VoterLandingPage: React.FC = () => {
  const nav = useNavigate();
  useEnsureVoter();
  const me = useVoterMe();

  const [rows, setRows] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);
        const r = await fetch('/voter/elections/active', { credentials: 'include' });
        const j = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(j.error || 'Failed to load elections');
        if (alive) setRows(j.elections || []);
      } catch (e: any) {
        if (alive) setErr(e.message || 'Failed to load elections');
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const empty = useMemo(() => !loading && !err && rows.length === 0, [loading, err, rows]);

  return (
    <div className="voter-landing">
      <main className="vl-main">
        {/* Header: only the title now */}
        <div className="vl-header-row">
          <h2>Your Voting Options</h2>
        </div>

        {/* LEFT COLUMN */}
        <section className="vl-left">
          {/* put the last-login chip on the LEFT */}
          <div className="vl-badge-inline">
            <LastLoginBadge me={me} />
          </div>

          {loading && (
            <div className="vl-grid">
              {[...Array(3)].map((_, i) => <div key={i} className="vl-card skeleton" />)}
            </div>
          )}

          {err && <div className="vl-error">{err}</div>}

          {empty && (
            <div className="vl-empty">
              <p>No active elections at the moment.</p>
              <p className="vl-subtle">Please check back later.</p>
            </div>
          )}

          {!loading && !err && rows.length > 0 && (
            <div className="vl-grid">
              {rows.map((e) => (
                <article key={e.id} className="vl-card">
                  <div className="vl-card-title">{e.name}</div>
                  <div className="vl-card-meta">
                    <div>ID: {e.id}</div>
                    <div>Starts: {e.start_time ? new Date(e.start_time).toLocaleString() : '—'}</div>
                    <div>Ends: {e.end_time ? new Date(e.end_time).toLocaleString() : '—'}</div>
                    <div>Candidates: {e.candidate_count ?? 0}</div>
                  </div>
                  <button
                    className="vl-start"
                    onClick={() => nav(`/voter/elections/${e.id}`)}
                    aria-label={`Start voting in ${e.name}`}
                  >
                    Start
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>

        {/* RIGHT TEAL SIDEBAR */}
        <VoterRightSidebar />
      </main>
    </div>
  );
};

export default VoterLandingPage;
