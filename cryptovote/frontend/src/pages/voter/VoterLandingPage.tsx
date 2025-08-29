import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/voter-landing.css';
import { useEnsureVoter } from '../../hooks/useAuthGuard';
import LastLoginBadge from '../../components/voter/LastLoginBadge';
import VoterRightSidebar from '../../components/voter/VoterRightSidebar';
import { useCredential } from '../../ctx/CredentialContext';
import { genToken, blindToken, unblindSignature, RsaPub } from '../../lib/cred';
import { useBackForwardLock } from '../../hooks/useBackForwardLock';

async function safeJson(res: Response) {
  try { return await res.json(); } catch { return {}; }
}

function normalizeRsaKey(raw: any): RsaPub {
  const key_id = raw?.key_id ?? raw?.id;
  const n_hex  = raw?.n_hex ?? raw?.nHex ?? raw?.n ?? raw?.modulusHex;
  const e_dec  = raw?.e_dec ?? raw?.eDec ?? (typeof raw?.e !== 'undefined' ? String(raw.e) : undefined);
  if (!key_id || !n_hex || !e_dec) throw new Error('Invalid RSA key format');
  return { key_id, n_hex, e_dec };
}

async function getRsaPub(rsaKeyId: string): Promise<RsaPub> {
  const res = await fetch('/public-keys', { credentials: 'include' });
  const body: any = await safeJson(res);
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);

  let candidates: any[] = [];
  if (Array.isArray(body?.rsa)) candidates = body.rsa;
  else if (body?.rsa && typeof body.rsa === 'object') candidates = [body.rsa];
  else if (body?.key_id || body?.nHex || body?.n_hex) candidates = [body];

  if (!candidates.length) throw new Error('No RSA keys available');

  const raw = candidates.find(k => (k?.key_id ?? k?.id) === rsaKeyId) ?? candidates[0];
  return normalizeRsaKey(raw);
}

type Election = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  candidate_count: number;
  rsa_key_id?: string;
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
  const { setCred } = useCredential();

  const [rows, setRows] = useState<Election[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  // Results & Audit lookup state
  const [lookupId, setLookupId] = useState('');
  const [resLoading, setResLoading] = useState(false);
  const [resErr, setResErr] = useState<string | null>(null);
  const [resData, setResData] = useState<any>(null);

  // UX helpers: toast + invalid input highlight
  const [toast, setToast] = useState<{ type: 'info' | 'error' | 'success'; msg: string } | null>(null);
  const [inputInvalid, setInputInvalid] = useState(false);

  function showToast(type: 'info' | 'error' | 'success', msg: string) {
    setToast({ type, msg });
    window.clearTimeout((showToast as any)._t);
    (showToast as any)._t = window.setTimeout(() => setToast(null), 3200);
  }

  function validateElectionId(raw: string) {
    const id = raw.trim();
    if (!id) return { ok: false, reason: 'Please enter an election ID.' };
    const ok =
      /^election[_-]ver[_-]?\d+$/i.test(id) ||
      /^[A-Za-z0-9_-]{3,64}$/.test(id);
    return ok
      ? { ok: true }
      : { ok: false, reason: 'Invalid ID. Use letters, numbers, - or _, 3–64 chars (e.g. election_ver_9).' };
  }

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

  const startElection = async (electionId: string) => {
    try {
      setBusyId(electionId);
      setErr(null);

      // 1) election detail
      const ed = await fetch(`/voter/elections/${electionId}`, { credentials: 'include' });
      const ej: any = await safeJson(ed);
      if (!ed.ok) throw new Error(ej.error || 'Failed to load election detail');
      const rsaKeyId: string = ej.rsa_key_id;

      // 2) public key (normalized)
      const pub = await getRsaPub(rsaKeyId);

      // 3) generate + blind
      const token = genToken();
      const { blindedHex, r } = await blindToken(token, pub);

      // 4) blind-sign
      const bs = await fetch(`/elections/${electionId}/blind-sign`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ blinded_token_hex: blindedHex, rsa_key_id: rsaKeyId })
      });
      const bj: any = await safeJson(bs);
      if (!bs.ok) throw new Error(bj.error || 'Blind-sign failed');

      const signedBlindedHex =
        bj.signed_blinded_token_hex ??
        bj.signed_blinded_token ??
        bj.signed ??
        null;
      if (!signedBlindedHex) throw new Error('Server did not return signed_blinded_token');

      // 5) unblind -> final signature
      const signatureHex = unblindSignature(signedBlindedHex, r, pub);

      // 6) store ephemeral cred + go ballot
      const credObj = { electionId, token, signatureHex, rsaKeyId };
      setCred(credObj);
      try { sessionStorage.setItem('ephemeral_cred', JSON.stringify(credObj)); } catch {}
      nav(`/voter/elections/${electionId}`, { state: { cred: credObj }, replace: true });
    } catch (e: any) {
      setErr(e.message || 'Failed to prepare credential');
    } finally {
      setBusyId(null);
    }
  };

  async function fetchResults(eid: string) {
    setResErr(null); setResData(null); setResLoading(true);
    try {
      const r = await fetch(`/results/${encodeURIComponent(eid)}`, { credentials: 'include' });
      const j = await safeJson(r);
      if (!r.ok) throw new Error(j.error || `Failed to fetch results for ${eid}`);
      setResData(j);
    } catch (e: any) {
      const msg = e?.message || 'Failed to fetch results';
      setResErr(msg);
      showToast('error', msg);
    } finally { setResLoading(false); }
  }

  async function downloadJson(url: string, filename: string) {
    const r = await fetch(url, { credentials: 'include' });
    if (!r.ok) {
      const j = await safeJson(r);
      const msg = j.error || `HTTP ${r.status}`;
      showToast('error', msg);
      throw new Error(msg);
    }
    let blob: Blob;
    try {
      const j = await r.clone().json();
      blob = new Blob([JSON.stringify(j, null, 2)], { type: 'application/json' });
    } catch {
      blob = await r.blob();
    }
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
    showToast('success', 'Download started.');
  }

  function onSubmitResults(e: React.FormEvent) {
    e.preventDefault();
    const { ok, reason } = validateElectionId(lookupId);
    if (!ok) {
      setInputInvalid(true);
      showToast('error', reason!);
      return;
    }
    setInputInvalid(false);
    if (!resLoading) fetchResults(lookupId.trim());
  }

    useBackForwardLock({
    enabled: true,
    onAttempt: () => showToast('info', 'Use the in-app navigation or Logout to leave.'),
  });

  return (
    <div className="voter-landing">
      <main className="vl-main">

        {/* Toast */}
        {toast && (
          <div className={`toast ${toast.type}`} role="alert" aria-live="assertive">
            {toast.msg}
          </div>
        )}

        {/* Header */}
        <div className="vl-header-row">
          <h2>Your Voting Options</h2>
        </div>

        {/* LEFT COLUMN */}
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
                    disabled={busyId === e.id}
                    onClick={() => startElection(e.id)}
                    aria-label={`Start voting in ${e.name}`}
                  >
                    {busyId === e.id ? 'Preparing…' : 'Start'}
                  </button>
                </article>
              ))}
            </div>
          )}

          {/* Results & Audit */}
          <div className="vl-card" style={{ marginTop: 16 }}>
            <div className="vl-card-title">Results &amp; Audit</div>

            {/* Enter-to-submit via form */}
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
                    onClick={() => downloadJson(`/results/${encodeURIComponent(lookupId)}/audit-bundle`, `audit_${lookupId}.json`)}
                  >
                    Download Audit Bundle
                  </button>
                  <button
                    className="vl-start"
                    title="Your acknowledgement of vote"
                    onClick={() => downloadJson(`/receipts/${encodeURIComponent(lookupId)}`, `receipt_${lookupId}.json`)}
                  >
                    Download My Receipt
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* RIGHT TEAL SIDEBAR */}
        <VoterRightSidebar />
      </main>
    </div>
  );
};

export default VoterLandingPage;
