import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../../styles/voter-landing.css';
import { useEnsureVoter } from '../../hooks/useAuthGuard';
import LastLoginBadge from '../../components/voter/LastLoginBadge';
import VoterRightSidebar from '../../components/voter/VoterRightSidebar';
import { useCredential } from '../../ctx/CredentialContext';
import { genToken, blindToken, unblindSignature, RsaPub } from '../../lib/cred';

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

  // Accept any of: {rsa:[...]}, {rsa:{...}}, or a single key at root.
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

  // --- Start flow: prepare blind-signed credential then go ballot ---
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
    const signatureHex = unblindSignature(bj.signed_blinded_token_hex, r, pub);

    // 6) store ephemeral cred + go ballot
    const credObj = { electionId, token, signatureHex, rsaKeyId };
    console.log('Prepared cred →', credObj);
    setCred(credObj);
    try { sessionStorage.setItem("ephemeral_cred", JSON.stringify(credObj)); } catch {}
    nav(`/voter/elections/${electionId}`, { state: { cred: credObj } });
  } catch (e: any) {
    setErr(e.message || 'Failed to prepare credential');
  } finally {
    setBusyId(null);
  }
};


  return (
    <div className="voter-landing">
      <main className="vl-main">
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
        </section>

        {/* RIGHT TEAL SIDEBAR */}
        <VoterRightSidebar />
      </main>
    </div>
  );
};

export default VoterLandingPage;
