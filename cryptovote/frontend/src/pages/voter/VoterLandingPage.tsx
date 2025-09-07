// src/pages/voter/VoterLandingPage.tsx
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/voter-landing.css';

import { useEnsureVoter } from '../../hooks/useAuthGuard';
import { useVoterMe } from '../../hooks/useVoterMe';
import { useInlineToast } from '../../hooks/useInlineToast';
import { useCredential } from '../../ctx/CredentialContext';
import { genToken, blindToken, unblindSignature } from '../../lib/cred';
import { genTrackerHex } from "../../lib/tracker";
import { useBackForwardLock } from '../../hooks/useBackForwardLock';

import LastLoginBadge from '../../components/voter/LastLoginBadge';
import VoterRightSidebar from '../../components/voter/VoterRightSidebar';
import ElectionCard from '../../components/voter/ElectionCard';

import { getRsaPub } from '../../services/voter/keys';
import { downloadJson } from '../../services/voter/http';
import {
  blindSign,
  fetchActiveElections,
  fetchElectionDetail,
  fetchResults,
  type Election
} from '../../services/voter/elections';

async function safeJson(res: Response) {
  try { return await res.json(); } catch { return {}; }
}

const VoterLandingPage: React.FC = () => {
  const nav = useNavigate();
  useEnsureVoter();
  const me = useVoterMe();
  const { setCred } = useCredential();
  const { toast, show } = useInlineToast();

  const [rows, setRows] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  // Results & Audit lookup state
  const [lookupId, setLookupId] = useState('');
  const [resLoading, setResLoading] = useState(false);
  const [resData, setResData] = useState<any>(null);

  // --- WBB verify state ---
  const [wbbElectionId, setWbbElectionId] = useState('');
  const [wbbTracker, setWbbTracker] = useState('');
  const [wbbLoading, setWbbLoading] = useState(false);
  const [wbbFound, setWbbFound] = useState<boolean | null>(null);
  const [wbbIndex, setWbbIndex] = useState<number | null>(null);
  const [wbbRoot, setWbbRoot] = useState<string | null>(null);
  const [wbbCount, setWbbCount] = useState<number | null>(null);

  // initial load
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true); setErr(null);
        const j = await fetchActiveElections();
        if (alive) setRows(j.elections || []);
      } catch (e: any) {
        if (alive) setErr(e?.message || 'Failed to load elections');
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const empty = useMemo(() => !loading && !err && rows.length === 0, [loading, err, rows]);

  // prepare blind-signed credential then navigate
  const startElection = async (electionId: string) => {
    try {
      setBusyId(electionId); setErr(null);
      const ej: any = await fetchElectionDetail(electionId);
      const rsaKeyId: string = ej.rsa_key_id;

      const pub = await getRsaPub(rsaKeyId);
      const token = genToken();
      const tracker = genTrackerHex(16); // 32 hex chars
      const { blindedHex, r } = await blindToken(token, pub);

      const bj = await blindSign(electionId, { blinded_token_hex: blindedHex, rsa_key_id: rsaKeyId });
      const signedBlindedHex =
        bj.signed_blinded_token_hex ?? bj.signed_blinded_token ?? bj.signed ?? null;
      if (!signedBlindedHex) throw new Error('Server did not return signed_blinded_token');

      const signatureHex = unblindSignature(signedBlindedHex, r, pub);

      const credObj = { electionId, token, signatureHex, rsaKeyId, tracker };
      setCred(credObj);
      try { sessionStorage.setItem('ephemeral_cred', JSON.stringify(credObj)); } catch {}
      nav(`/voter/elections/${electionId}`, { state: { cred: credObj }, replace: true });
    } catch (e: any) {
      setErr(e?.message || 'Failed to prepare credential');
    } finally {
      setBusyId(null);
    }
  };

  async function onSubmitResults(e: React.FormEvent) {
    e.preventDefault();
    const id = lookupId.trim();
    if (!id) { show('error', 'Please enter an election ID.'); return; }
    setResData(null); setResLoading(true);
    try {
      const j = await fetchResults(id);
      setResData(j);
    } catch (err: any) {
      show('error', err?.message || 'Failed to fetch results');
    } finally {
      setResLoading(false);
    }
  }

  // --- WBB verify handler (uses new /proof shape) ---
  async function verifyOnWBB(e: React.FormEvent) {
    e.preventDefault();
    const eid = wbbElectionId.trim();
    const tkr = wbbTracker.trim();
    if (!eid) { show('error', 'Enter election ID.'); return; }
    if (!tkr) { show('error', 'Enter your tracker.'); return; }

    setWbbFound(null);
    setWbbIndex(null);
    setWbbRoot(null);
    setWbbCount(null);
    setWbbLoading(true);

    try {
      const r = await fetch(`/wbb/${encodeURIComponent(eid)}/proof?tracker=${encodeURIComponent(tkr)}`, {
        credentials: 'include'
      });
      const j = await safeJson(r);
      if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);

      if (j.found) {
        setWbbFound(true);
        setWbbIndex(j.entry?.index ?? null);
        setWbbRoot(j.entry?.root ?? null);
        setWbbCount(j.count ?? null);
        show('success', `Vote is Included ✓`);
      } else {
        setWbbFound(false);
        setWbbRoot(j.root ?? null);
        setWbbCount(j.count ?? null);
        show('error', 'Invalid election id or tracker id.');
      }
    } catch (e: any) {
      show('error', e?.message || 'Verification failed');
    } finally {
      setWbbLoading(false);
    }
  }

  useBackForwardLock({
    enabled: true,
    onAttempt: () => show('info', 'Use the in-app navigation or Logout to leave.'),
  });

  return (
    <div className="voter-landing">
      <main className="vl-main">
        {toast && (
          <div className={`toast ${toast.type}`} role="alert" aria-live="assertive">
            {toast.msg}
          </div>
        )}

        <div className="vl-header-row">
          <h2>Your Voting Options</h2>
        </div>

        <section className="vl-left">
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
                <ElectionCard key={e.id} e={e} busy={busyId === e.id} onStart={startElection} />
              ))}
            </div>
          )}

          {/* Results & Audit */}
          <div className="vl-card" style={{ marginTop: 16 }}>
            <div className="vl-card-title">Voting Results</div>

            <form className="inline-field" onSubmit={onSubmitResults}>
              <input
                id="eid"
                className="vl-input"
                placeholder="e.g. election_ver_1"
                value={lookupId}
                onChange={e => setLookupId(e.target.value)}
                aria-label="Election ID"
              />
              <button
                type="submit"
                className="vl-start"
                disabled={resLoading || !lookupId.trim()}
                aria-label="View results"
              >
                {resLoading ? 'Checking…' : 'View Results'}
              </button>
            </form>

            {resData && (
              <div style={{ marginTop: 12 }}>
                <div className="vl-card-title" style={{ fontSize: 16 }}>
                  {resData.election?.name || resData.election?.id} — {resData.status === 'final' ? 'Final' : 'Pending'}
                </div>
                <div className="vl-card-meta" style={{ marginTop: 8 }}>
                  <div>Last updated: {resData.last_updated ? new Date(resData.last_updated).toLocaleString() : '—'}</div>
                </div>

                <div style={{ marginTop: 10 }}>
                  <table className="vl-table">
                    <thead><tr><th>Candidate</th><th>Total</th><th></th></tr></thead>
                    <tbody>
                      {(resData.candidates || []).map((c: any) => {
                        const isWinner = (resData.winner_ids || []).includes(c.id);
                        return (
                          <tr key={c.id}>
                            <td>{c.name}</td>
                            <td>{c.total ?? '—'}</td>
                            <td>{isWinner ? <span className="badge">Winner</span> : null}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button
                    className="vl-start"
                    onClick={async () => {
                      try { await downloadJson(`/results/${encodeURIComponent(lookupId)}/audit-bundle`, `audit_${lookupId}.json`); }
                      catch (e:any) { show('error', e?.message || 'Download failed'); }
                    }}
                  >
                    Download Audit Bundle
                  </button>
                  <button
                    className="vl-start"
                    title="Your acknowledgement of vote"
                    onClick={async () => {
                      try { await downloadJson(`/receipts/${encodeURIComponent(lookupId)}`, `receipt_${lookupId}.json`); }
                      catch (e:any) { show('error', e?.message || 'Download failed'); }
                    }}
                  >
                    Download My Receipt
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* ---- WBB Verify ---- */}
          <div className="vl-card" style={{ marginTop: 16 }}>
            <div className="vl-card-title">Ballot Verification</div>
            <form className="inline-field" onSubmit={verifyOnWBB}>
              <input
                className="vl-input"
                placeholder="e.g. election_ver_1"
                value={wbbElectionId}
                onChange={e => setWbbElectionId(e.target.value)}
                aria-label="Election ID for verification"
              />
              <input
                className="vl-input"
                placeholder="Your tracker (hex)"
                value={wbbTracker}
                onChange={e => setWbbTracker(e.target.value)}
                aria-label="Tracker"
              />
              <button
                type="submit"
                className="vl-start"
                disabled={wbbLoading || !wbbElectionId.trim() || !wbbTracker.trim()}
                aria-label="Verify on WBB"
              >
                {wbbLoading ? 'Verifying…' : 'Verify on WBB'}
              </button>
            </form>

            {(wbbFound !== null) && (
              <div className="vl-card-meta" style={{ marginTop: 10, wordBreak: 'break-all' }}>
                {wbbFound ? (
                  <>
                    <div>Inclusion: <strong>Yes</strong> ✅</div>
                    <div>Merkle Root: <code>{wbbRoot ?? '—'}</code></div>
                  </>
                ) : (
                  <>
                    <div>Inclusion: <strong>No</strong> (not found)</div>
                    {typeof wbbCount === 'number' && <div>Current entries: {wbbCount}</div>}
                    {wbbRoot && <div>Merkle Root: <code>{wbbRoot}</code></div>}
                  </>
                )}
              </div>
            )}
          </div>
          {/* ---- /WBB Verify ---- */}
        </section>

        <VoterRightSidebar />
      </main>
    </div>
  );
};

export default VoterLandingPage;
