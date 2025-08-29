import React, { useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import LeftSidebar from '../../components/admin/AdminLeftSideBar'; // adjust path if yours is /ui/...
import Toast from '../../components/ui/Toast';
import ConfirmationModal from '../../components/auth/ConfirmationModal';

import { useElectionStatus } from '../../hooks/useElectionStatus';
import { useToast } from '../../hooks/useToast';
import { buildActions } from '../../components/admin/buildActions';
import StatusPanel from '../../components/admin/StatusPanel';
import { prettyState } from '../../utils/format';

import ActionColumn from '../../components/admin/ActionColumn';

import '../../styles/admin-landing.css';
import '../../styles/admin-election.css';

import type { ModalKind } from '../../services/admin/types';

const AdminElectionPage: React.FC = () => {
  const { electionId = '' } = useParams();
  const navigate = useNavigate();

  const { status, loading, refresh } = useElectionStatus(electionId);
  const { toast, show } = useToast();

  const [panelOpen, setPanelOpen] = useState(true);
  const [busy, setBusy] = useState<ModalKind | null>(null);
  const [confirm, setConfirm] = useState<ModalKind | null>(null);
  const [reportFormat, setReportFormat] = useState<'pdf'|'csv'>('pdf');

  const actions = useMemo(
    () => buildActions({
      electionId,
      status,
      reportFormat,
      onAfter: refresh,
      toast: show,
    }),
    [electionId, status, reportFormat, refresh, show]
  );

  const chipClass = !status ? 'mgr-chip--dim'
    : status.has_ended ? 'mgr-chip--ended'
    : status.is_active ? 'mgr-chip--active'
    : status.has_started ? 'mgr-chip--running'
    : 'mgr-chip--dim';

  const labels = {
    start: actions.start.label(busy === 'start'),
    end:   actions.end.label(busy === 'end'),
    tally: actions.tally.label(busy === 'tally'),
    report:actions.report.label(busy === 'report'),
  };
  const disabled = {
    start: actions.start.disabled,
    end:   actions.end.disabled,
    tally: actions.tally.disabled,
    report:actions.report.disabled,
  };

  async function onConfirm() {
    const k = confirm;
    setConfirm(null);
    if (!k) return;
    try { setBusy(k); await actions[k].run(); }
    catch (e:any) { show('error', e?.message || 'Action failed.'); }
    finally { setBusy(null); }
  }

  return (
    <div className="admin-landing">
      <LeftSidebar title="Election Management" />
      <main className="right-panel">
        <header className="mgr-header">
          <button className="mgr-btn-ghost" onClick={() => navigate('/admin/landing')}>← Back</button>
          <h2 className="mgr-header__title">{status?.name ?? 'Election'}</h2>
          {!!status && <span className={['mgr-chip', chipClass].join(' ')}>{prettyState(status)}</span>}
        </header>

        {loading && <div>Loading election…</div>}

        {!loading && status && (
          <section className={`mgr-grid ${panelOpen ? 'with-panel' : 'full-width'}`}>
            {/* Actions */}
            <ActionColumn
              status={status}
              busy={busy}
              onOpen={(k) => (k === 'report' ? setConfirm('report') : setConfirm(k))}
              reportFormat={reportFormat}
              setReportFormat={setReportFormat}
              labels={labels}
              disabled={disabled}
              dangerEnd
            />

            {/* Status panel */}
            {panelOpen && (
              <StatusPanel s={status} electionId={electionId} onClose={() => setPanelOpen(false)} />
            )}
          </section>
        )}

        {toast && (
          <Toast type={toast.type} message={toast.msg} duration={3000} onClose={() => {/* auto-clears */}} />
        )}

        <ConfirmationModal
          isOpen={!!confirm}
          title={confirm ? actions[confirm].title : ''}
          message={confirm ? actions[confirm].message : ''}
          onConfirm={onConfirm}
          onCancel={() => setConfirm(null)}
        />
      </main>
    </div>
  );
};

export default AdminElectionPage;
