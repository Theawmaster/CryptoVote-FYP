// src/pages/voter/VoteCompletePage.tsx
import React, { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import VoterRightSidebar from "../../components/voter/VoterRightSidebar";
import "../../styles/voter-landing.css";
import completeGif from "../../assets/logo/complete.gif";

async function safeJson(res: Response) {
  try { return await res.json(); } catch { return {}; }
}

const VoteCompletePage: React.FC = () => {
  const nav = useNavigate();
  const { id: electionId = "" } = useParams<{ id: string }>();
  const loc = useLocation() as { state?: { electionName?: string; electionId?: string; tracker?: string } };
  const name = loc?.state?.electionName ?? "Election";
  const tracker = loc?.state?.tracker ?? null;

  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);

  async function downloadReceipt() {
    try {
      const qs = new URLSearchParams({
        election_name: name,
        election_id: electionId || "unknown",
        tracker: tracker || "",
      });
      const r = await fetch(`/voter/receipt?${qs.toString()}`, {
        credentials: "include",
      });
      if (!r.ok) {
        alert("Couldn’t generate receipt.");
        return;
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const cd = r.headers.get("content-disposition");
      const match = cd && /filename="([^"]+)"/i.exec(cd);
      a.download = match?.[1] ?? `vote_receipt_${electionId || "unknown"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      nav("/voter", { replace: true });
    } catch {
      alert("Download failed.");
    }
  }

  async function quickVerify() {
    if (!tracker) return;
    setVerifying(true);
    try {
      const url = `/wbb/${encodeURIComponent(electionId)}/proof?tracker=${encodeURIComponent(tracker)}`;
      const r = await fetch(url, { credentials: "include" });
      const j = await safeJson(r);
      if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
      if (j.found) {
        const idx = j.entry?.index ?? "—";
        alert(`Included ✓ (index ${idx})\nRoot: ${j.entry?.root || "—"}`);
      } else {
        alert("Not found yet. Try again in a minute.");
      }
    } catch {
      alert("Network error.");
    } finally {
      setVerifying(false);
    }
  }

  function copyTracker() {
    if (!tracker) return;
    navigator.clipboard?.writeText(tracker).then(
      () => alert("Tracker copied."),
      () => alert(tracker) // fallback: show it so user can copy manually
    );
  }

  return (
    <div className="voter-landing">
      <main className="vl-main">
        <section className="vl-left">
          <div className="vl-header-row" style={{ justifyContent: "center" }}>
            <h2 style={{ margin: 0, textAlign: "center" }}>{name}</h2>
          </div>

          <div
            className="vl-card"
            style={{
              maxWidth: 760,
              marginInline: "auto",
              padding: 24,
              textAlign: "center",
            }}
          >
            <div className="vl-card-title" style={{ textAlign: "center" }}>
              Thank you for submitting your vote
            </div>
            <p style={{ marginTop: 4, color: "var(--muted-fg, #666)" }}>
              Your vote has been recorded.
            </p>

            <div style={{ display: "flex", justifyContent: "center", margin: "18px 0 6px" }}>
              <img
                src={completeGif}
                alt="Vote completed"
                style={{
                  width: 340,
                  height: 340,
                  objectFit: "contain",
                  borderRadius: 9999,
                }}
              />
            </div>

            {/* Tracker utilities */}
            {tracker && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 14, color: "#666", marginBottom: 6 }}>
                  Your tracker (keep this to verify on the bulletin board):
                </div>
                <code style={{ display: "block", wordBreak: "break-all" }}>{tracker}</code>
                <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 8, flexWrap: "wrap" }}>
                  <button className="btn btn-outline" onClick={copyTracker}>Copy tracker</button>
                  <button className="btn btn-outline" onClick={quickVerify} disabled={verifying}>
                    {verifying ? "Verifying…" : "Verify on WBB"}
                  </button>
                </div>
              </div>
            )}

            <div
              style={{
                display: "flex",
                gap: 16,
                justifyContent: "center",
                marginTop: 16,
                flexWrap: "wrap",
              }}
            >
              <button className="btn btn-outline" onClick={downloadReceipt}>
                Download receipt
              </button>
              <button
                className="btn btn-primary"
                onClick={() => nav("/voter", { replace: true })}
                disabled={sending}
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </section>

        <VoterRightSidebar />
      </main>
    </div>
  );
};

export default VoteCompletePage;
