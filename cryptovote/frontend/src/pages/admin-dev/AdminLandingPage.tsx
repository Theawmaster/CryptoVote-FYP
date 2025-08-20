import React, { useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import LeftSidebar from '../../components/admin/AdminLeftSideBar';
import CreateElectionForm from '../../components/form/CreateElectionForm';

import { useAdminMe, useElections, useSuspicious } from '../../hooks/admin';
import LastLoginBadge from '../../components/admin/LastLoginBadge';
import ElectionCard from '../../components/admin/ElectionCard';
import { SecurityBell, SuspiciousDrawer } from '../../components/admin/SuspiciousDrawer';
import { apiDownload } from '../../services/api';

import '../../styles/admin-landing.css';

type FilterKey = 'all' | 'active' | 'ended' | 'upcoming';

export default function AdminLandingPage() {
  const navigate = useNavigate();
  const email = (useLocation().state?.email as string | undefined);

  const me = useAdminMe();
  const { data: elections, loading, err } = useElections();
  const [filter, setFilter] = useState<FilterKey>('all');
  const [showCreate, setShowCreate] = useState(false);

  const sec = useSuspicious();

  const filtered = useMemo(() => {
    if (!elections) return [];
    switch (filter) {
      case 'active':   return elections.filter(e => e.is_active);
      case 'ended':    return elections.filter(e => e.has_ended);
      case 'upcoming': return elections.filter(e => !e.has_started);
      default:         return elections;
    }
  }, [elections, filter]);

  function onMore(id: string) { navigate(`/admin/manage/${id}`, { state: { email } }); }

  // exports (reusing apiDownload)
  async function exportCsv() { await apiDownload('/admin/security/suspicious.csv', 'suspicious.csv'); }
  async function exportPdf() { await apiDownload('/admin/security/suspicious.pdf', 'suspicious.pdf'); }

  return (
    <div className="admin-landing">
      <LeftSidebar title="Admin Landing Page" />
      <main className="right-panel">
        <div className="mgr-header-row">
          <h2>Your Voting Campaigns</h2>
          <div className="flex items-center gap-3">
            <LastLoginBadge me={me} />
            <SecurityBell count={sec.count} onClick={() => { sec.setOpen(true); sec.loadList(); }} />
          </div>
        </div>

        <div className="filter-bar">
          {(['all','active','ended','upcoming'] as FilterKey[]).map(key => (
            <button key={key} className={`filter-pill ${filter === key ? 'active' : ''}`} onClick={() => setFilter(key)}>
              {key[0].toUpperCase() + key.slice(1)}
            </button>
          ))}
        </div>

        {loading && (
          <div className="skeleton-grid">
            {[...Array(3)].map((_,i)=><div key={i} className="skeleton-card" />)}
          </div>
        )}

        {err && <div style={{ color:'crimson' }}>{err}</div>}

        {!loading && !err && (
          <>
            <div className="elections-grid">
              {filtered.map((e) => <ElectionCard key={e.id} e={e} onMore={onMore} />)}
            </div>

            <div className="create-section" onClick={() => {
              setShowCreate(true);
              setTimeout(() => document.getElementById('create-election-anchor')?.scrollIntoView({ behavior: 'smooth' }), 0);
            }}>
              <div className="create-card">+ Create new</div>
            </div>

            {showCreate && (
              <CreateElectionForm onCreated={(e) => {
                // optimistic prepend
                // optional: refetch in useElections hook instead
                // setElections(prev => [e, ...prev]);  // if you keep local state
                setShowCreate(false);
              }} />
            )}
          </>
        )}

        <SuspiciousDrawer
          open={sec.open}
          onClose={() => sec.setOpen(false)}
          items={sec.items}
          loading={sec.loading}
          onRefresh={() => sec.loadList()}
          onExportCsv={exportCsv}
          onExportPdf={exportPdf}
        />
      </main>
    </div>
  );
}
