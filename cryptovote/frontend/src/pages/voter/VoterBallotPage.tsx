// src/pages/voter/VoterBallotPage.tsx
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useEnsureVoter } from "../../hooks/useAuthGuard";
import { useCredential } from "../../ctx/CredentialContext";
import { genTrackerHex } from "../../lib/tracker";
import { useBackForwardLock } from "../../hooks/useBackForwardLock";
import VoterRightSidebar from "../../components/voter/VoterRightSidebar";
import ConfirmationModal from "../../components/auth/ConfirmationModal";
import ConfirmLeaveModal from "../../components/auth/ConfirmLeaveModal";

import { E2EE_ENABLED } from "../../config/flags";
import { usePaillierKey } from "../../hooks/usePaillierKey";
import { fetchElectionDetailBallot } from "../../services/voter/elections";
import {
  buildOneHotBallot,
  submitE2EE,
  submitLegacy,
  type ElectionDetail as Detail,
} from "../../services/voter/ballot";

import "../../styles/voter-landing.css";

async function safeJson(res: Response) {
  try { return await res.json(); } catch { return {}; }
}

const VoterBallotPage: React.FC = () => {
  useEnsureVoter();
  const nav = useNavigate();
  const { id: electionId = "" } = useParams<{ id: string }>();
  const location = useLocation() as { state?: any };

  const { cred, setCred, clear } = useCredential();

  // ---------- state ----------
  const [checked, setChecked] = useState(false);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [selected, setSelected] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const [showBackConfirm, setShowBackConfirm] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const onAttempt = useCallback(() => setShowConfirm(true), []);

  // E2EE key (only fetched when flag is on)
  const { nDec, keyId } = usePaillierKey(!!E2EE_ENABLED);

  // ---------- hydrate cred from nav state / sessionStorage ----------
  useEffect(() => {
    let next = cred ?? location?.state?.cred ?? null;
if (!next) {
      try {
        const raw = sessionStorage.getItem("ephemeral_cred");
        if (raw) next = JSON.parse(raw);
      } catch {}
    }
    if (!next) return;

    // ensure tracker exists
    if (!next.tracker) {
      next = { ...next, tracker: genTrackerHex(16) };
    }

    setCred(next);
    try { sessionStorage.setItem("ephemeral_cred", JSON.stringify(next)); } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location?.state?.cred, setCred]);

  // allow context to settle before showing guards
  useEffect(() => {
    const t = setTimeout(() => setChecked(true), 0);
    return () => clearTimeout(t);
  }, []);

  // ---------- load election detail ----------
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true); setErr(null);
        const j = await fetchElectionDetailBallot(electionId);
        if (alive) setDetail(j);
      } catch (e: any) {
        if (alive) setErr(e?.message || "Failed to load election");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [electionId]);

  const disabled = useMemo(() => submitting || confirming || done, [submitting, confirming, done]);

  // ---------- back flow ----------
  function requestBack() {
    if (done) nav("/voter");
    else setShowBackConfirm(true);
  }
  function confirmBack() {
    clear();
    try { sessionStorage.removeItem("ephemeral_cred"); } catch {}
    setShowBackConfirm(false);
    nav("/voter");
  }

  // ---------- cast vote ----------
  async function onConfirmCast() {
    if (!cred || !selected) return;
    try {
      setSubmitting(true);
      setErr(null);

      const base = {
        election_id: electionId,
        token: cred.token,
        signature: cred.signatureHex,
        tracker: cred.tracker,          // <<< REQUIRED by backend
      };

      // Prefer E2EE if key loaded; otherwise legacy server-side enc
      if (!(E2EE_ENABLED && nDec && keyId && detail)) {
        throw new Error("Client encryption not ready (missing key)"); // visible toast
      }
      const ballot = buildOneHotBallot(detail, selected, nDec, keyId);
      await submitE2EE({ ...base, ballot });

      setDone(true);
      clear();
      const tracker = cred.tracker;
      try { sessionStorage.removeItem("ephemeral_cred"); } catch {}
      nav(`/voter/elections/${electionId}/complete`, {
        replace: true,
        state: { electionName: detail?.name ?? "Election", electionId, tracker},
      });
    } catch (e: any) {
      setErr(e?.message || "Failed to cast vote");
    } finally {
      setSubmitting(false);
      setConfirming(false);
    }
  }

  // lock while on ballot
  useBackForwardLock({
    enabled: true,
    onAttempt,
    beforeUnloadMessage: "You have an in-progress ballot. Leave?",
  });

  const stay = () => setShowConfirm(false);
  const leave = async () => {
    try { await fetch("/logout/", { method: "POST", credentials: "include" }); } catch {}
    nav("/auth", { replace: true });
  };

  // ---------- render ----------
  return (
    <div className="voter-landing">
      <ConfirmLeaveModal open={showConfirm} onStay={stay} onLeave={leave} />
      <main className="vl-main">
        <section className="vl-left">
          <div className="ballot-header-bar">
            <button className="btn btn-outline" onClick={requestBack} aria-label="Back to options">← Back</button>
            <h1 className="ballot-title-center">{detail?.name ?? "Election"}</h1>
            <div />
          </div>

          {!checked && (
            <div className="vl-grid">
              {[...Array(2)].map((_, i) => <div key={i} className="vl-card skeleton" />)}
            </div>
          )}

          {checked && !cred && (
            <div className="vl-card" style={{ maxWidth: 560 }}>
              <div className="vl-card-title">Prepare credential first</div>
              <p>You’ll need a fresh blind-signed credential to open this ballot.</p>
              <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
                <button className="btn btn-primary" onClick={() => nav("/voter")}>Back to Voting Options</button>
              </div>
            </div>
          )}

          {checked && cred && cred.electionId !== electionId && (
            <div className="vl-card" style={{ maxWidth: 560 }}>
              <div className="vl-card-title">This credential is for a different election</div>
              <p>Prepared for <code>{cred.electionId}</code>, but you opened <code>{electionId}</code>.</p>
              <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
                <button className="btn btn-outline" onClick={() => nav(`/voter/elections/${cred.electionId}`)}>
                  Go to prepared ballot
                </button>
                <button className="btn btn-primary" onClick={() => nav("/voter")}>
                  Pick an election
                </button>
              </div>
            </div>
          )}

          {checked && cred && cred.electionId === electionId && (
            <>
              {loading && (
                <div className="vl-grid">
                  {[...Array(2)].map((_, i) => <div key={i} className="vl-card skeleton" />)}
                </div>
              )}

              {err && <div className="vl-error">{err}</div>}

              {!loading && !err && !done && detail && (
                <div className="ballot-card ballot-card--wide">
                  <div className="ballot-list">
                    {detail.candidates.map((c) => (
                      <div key={c.id} className={`ballot-row ${selected === c.id ? "is-selected" : ""}`}>
                        <div className="ballot-name">{c.name}</div>
                        <div className="ballot-actions">
                          <button
                            className="btn btn-primary ballot-vote-btn"
                            onClick={() => { setSelected(c.id); setConfirming(true); }}
                            disabled={disabled}
                            aria-label={`Vote for ${c.name}`}
                          >
                            ✓ Vote
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {confirming && selected && !done && (
                <div className="vl-card" role="dialog" aria-modal="true" style={{ maxWidth: 560 }}>
                  <div className="vl-card-title">Confirm your choice</div>
                  <p>Cast your vote for <strong>{detail?.candidates.find(x => x.id === selected)?.name}</strong>?</p>
                  <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
                    <button className="btn btn-outline" onClick={() => setConfirming(false)} disabled={submitting}>Cancel</button>
                    <button className="btn btn-primary" onClick={onConfirmCast} disabled={submitting}>
                      {submitting ? "Submitting…" : "Confirm & Cast"}
                    </button>
                  </div>
                </div>
              )}

              {done && (
                <div className="ballot-complete vl-card" style={{ maxWidth: 640 }}>
                  <div className="vl-card-title">{detail?.name ?? "Election"}</div>
                  <p>Thank you for submitting your vote.</p>
                  <div className="complete-icon" aria-hidden />
                  <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
                    <button className="btn btn-outline" onClick={() => alert("Email acknowledgement coming soon")}>
                      Send acknowledgement
                    </button>
                    <button className="btn btn-primary" onClick={() => nav("/voter")}>
                      Back to Dashboard
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        <VoterRightSidebar />
      </main>

      <ConfirmationModal
        isOpen={showBackConfirm}
        title="Leave this ballot?"
        message="If you go back now, your temporary credential will be cleared and you won’t be able to re-enter this ballot unless you prepare a new credential."
        onConfirm={confirmBack}
        onCancel={() => setShowBackConfirm(false)}
      />
    </div>
  );
};

export default VoterBallotPage;
