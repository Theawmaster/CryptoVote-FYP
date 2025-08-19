// src/pages/admin/AdminElectionPage.tsx
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import LeftSidebar from '../../components/ui/AdminLeftSideBar';
import Toast from '../../components/ui/Toast';
import ConfirmationModal from '../../components/auth/ConfirmationModal';

import {
  getElectionStatus,
  startElection,
  endElection,
  tallyElection,        // NEW
  downloadReportFile,   // NEW
} from '../../services/admin/electionActions';

import '../../styles/admin-landing.css';
import '../../styles/admin-election.css';

type Status = {
  id: string;
  name: string;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  start_time: string | null;
  end_time: string | null;
  tally_generated: boolean;
  candidate_count?: number;
  vote_count?: number;
};

type ModalKind = null | 'start' | 'end' | 'tally' | 'report';

const AdminElectionPage: React.FC = () => {
  const { electionId = '' } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<Status | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; msg: string } | null>(null);
  const [showStatusPanel, setShowStatusPanel] = useState(true);
  const [busy, setBusy] = useState<null | 'start' | 'end' | 'tally' | 'report'>(null);
  const [confirmModal, setConfirmModal] = useState<ModalKind>(null);
  const [reportFormat, setReportFormat] = useState<'pdf'|'csv'>('pdf');

  const showToast = (type: 'success' | 'error' | 'info', msg: string, ms = 3000) => {
    setToast({ type, msg });
    window.setTimeout(() => setToast(null), ms);
  };

  const refresh = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const s = await getElectionStatus(electionId);
      setStatus(s);
    } catch (e: any) {
      if (e?.name !== 'AbortError') showToast('error', e?.message || 'Failed to load status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!electionId) return;
    const c = new AbortController();
    refresh(c.signal);
    return () => c.abort();
  }, [electionId]);

  // --- Action calls (no prompts here) ---
  const doStart = async () => {
    setBusy('start');
    try {
      await startElection(electionId);
      showToast('success', 'Election started.');
      await refresh();
    } catch (e:any) {
      showToast('error', e?.message || 'Failed to start election.');
    } finally {
      setBusy(null);
    }
  };

  const doEnd = async () => {
    setBusy('end');
    try {
      await endElection(electionId);
      showToast('success', 'Election ended.');
      await refresh();
    } catch (e:any) {
      showToast('error', e?.message || 'Failed to end election.');
    } finally {
      setBusy(null);
    }
  };

  const doTally = async () => {
    setBusy('tally');
    try {
      const res = await tallyElection(electionId);
      // res.tally, res.zkp_proofs are available if you want to show a modal of results
      showToast('success', 'Tally generated.');
      await refresh();
    } catch (e:any) {
      showToast('error', e?.message || 'Failed to tally election.');
    } finally {
      setBusy(null);
    }
  };

  const doDownloadReport = async () => {
    setBusy('report');
    try {
      await downloadReportFile(electionId, reportFormat); // triggers browser download
      showToast('success', `Report (${reportFormat.toUpperCase()}) downloaded.`);
    } catch (e:any) {
      showToast('error', e?.message || 'Failed to download report.');
    } finally {
      setBusy(null);
    }
  };

  // --- Modal text / confirm handler ---
  const modalTitle =
    confirmModal === 'start' ? 'Start Election' :
    confirmModal === 'end'   ? 'End Election'   :
    confirmModal === 'tally' ? 'Tally Election' :
    confirmModal === 'report'? 'Generate Report' :
    '';

  const modalMessage =
    confirmModal === 'start'
      ? `Start "${status?.name ?? 'this election'}" now? This will mark it as Active.`
    : confirmModal === 'end'
      ? `End "${status?.name ?? 'this election'}" now? This action cannot be undone.`
    : confirmModal === 'tally'
      ? `Generate the homomorphic tally for "${status?.name ?? 'this election'}"? This requires the election to have ended.`
    : confirmModal === 'report'
      ? `Generate a ${reportFormat.toUpperCase()} report for "${status?.name ?? 'this election'}"?`
    : '';

  const onConfirmModal = async () => {
    const kind = confirmModal;
    setConfirmModal(null);
    if (kind === 'start') await doStart();
    if (kind === 'end')   await doEnd();
    if (kind === 'tally') await doTally();
    if (kind === 'report') await doDownloadReport();
  };

  const prettyState =
    !status ? '' :
    status.has_ended ? 'Ended' :
    status.is_active ? 'Active' :
    status.has_started ? 'Running' :
    'Not started';

  return (
    <div className="admin-landing">
      <LeftSidebar title="Election Management" />

      <main className="right-panel">
        {/* Top bar: back + centered name + chip on the right */}
        <header className="mgr-header">
          <button className="mgr-btn-ghost" onClick={() => navigate(-1)}>← Back</button>

          <h2 className="mgr-header__title">
            {status?.name ?? 'Election'}
          </h2>

          {!!status && (
            <span
              className={[
                'mgr-chip',
                status.has_ended ? 'mgr-chip--ended' :
                status.is_active ? 'mgr-chip--active' :
                status.has_started ? 'mgr-chip--running' :
                'mgr-chip--dim'
              ].join(' ')}
            >
              {prettyState}
            </span>
          )}
        </header>

        {loading && <div>Loading election…</div>}

        {!loading && status && (
          <section className={`mgr-grid ${showStatusPanel ? 'with-panel' : 'full-width'}`}>
            {/* Actions column */}
            <div className="mgr-actions">
              <h3 className="mgr-actions__title">{status.name}</h3>

              <button
                className="mgr-btn"
                disabled={status.has_started || busy === 'start'}
                onClick={() => setConfirmModal('start')}
              >
                {busy === 'start' ? 'Starting…' : 'Start Election'}
              </button>

              <button
                className="mgr-btn mgr-btn--outline"
                onClick={() => setShowStatusPanel(true)}
                aria-pressed={showStatusPanel}
              >
                Election Status
              </button>

              <button
                className="mgr-btn mgr-btn--danger"
                disabled={!status.is_active || status.has_ended || busy === 'end'}
                onClick={() => setConfirmModal('end')}
              >
                {busy === 'end' ? 'Ending…' : 'End Election'}
              </button>

              <button
                className="mgr-btn"
                disabled={!status.has_ended || busy === 'tally' || !!status.tally_generated}
                onClick={() => setConfirmModal('tally')}
                title={!status.has_ended ? 'End election first' : status.tally_generated ? 'Tally already generated' : ''}
              >
                {busy === 'tally' ? 'Tallying…' : (status.tally_generated ? 'Tally Generated' : 'Tally Election')}
              </button>

              <div className="mgr-report-row">
                <button
                  className="mgr-btn"
                  disabled={!status.tally_generated || busy === 'report'}
                  onClick={() => setConfirmModal('report')}
                  title={!status.tally_generated ? 'Generate tally first' : ''}
                >
                  {busy === 'report' ? 'Preparing…' : 'Generate Report'}
                </button>

                <select
                  className="mgr-select"
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as 'pdf'|'csv')}
                  aria-label="Report format"
                >
                  <option value="pdf">PDF</option>
                  <option value="csv">CSV</option>
                </select>
              </div>
            </div>

            {/* Status panel */}
            {showStatusPanel && (
              <div className="mgr-panel" role="region" aria-label="Election Status">
                <div className="mgr-panel__head">
                  <div>Election Status</div>
                  <button
                    className="mgr-panel__close"
                    onClick={() => setShowStatusPanel(false)}
                    aria-label="Close status panel"
                  >
                    ×
                  </button>
                </div>

                <dl className="mgr-kv">
                  <div><dt>Election</dt><dd>{status.name ?? '—'}</dd></div>
                  <div><dt>State</dt><dd>{prettyState}</dd></div>
                  <div><dt>Has started</dt><dd>{String(!!status.has_started)}</dd></div>
                  <div><dt>Has ended</dt><dd>{String(!!status.has_ended)}</dd></div>
                  <div><dt>Start time</dt><dd>{status.start_time ? new Date(status.start_time).toLocaleString() : '—'}</dd></div>
                  <div><dt>End time</dt><dd>{status.end_time ? new Date(status.end_time).toLocaleString() : '—'}</dd></div>
                  <div><dt>Tally generated</dt><dd>{String(!!status.tally_generated)}</dd></div>
                  <div><dt>ID</dt><dd>{status.id ?? electionId}</dd></div>
                  <div><dt>Candidate count</dt><dd>{status.candidate_count ?? 0}</dd></div>
                  <div><dt>Total votes</dt><dd>{status.vote_count ?? 0}</dd></div>
                </dl>
              </div>
            )}
          </section>
        )}

        {toast && (
          <Toast
            type={toast.type}
            message={toast.msg}
            duration={3000}
            onClose={() => setToast(null)}
          />
        )}

        {/* Reusable confirm modal */}
        <ConfirmationModal
          isOpen={!!confirmModal}
          title={modalTitle}
          message={modalMessage}
          onConfirm={onConfirmModal}
          onCancel={() => setConfirmModal(null)}
        />
      </main>
    </div>
  );
};

export default AdminElectionPage;
