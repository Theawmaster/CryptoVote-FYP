// src/pages/voter/VoteCompletePage.tsx
import React, { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import VoterRightSidebar from "../../components/voter/VoterRightSidebar";
import "../../styles/voter-landing.css";
import completeGif from "../../assets/logo/complete.gif";

const VoteCompletePage: React.FC = () => {
  const nav = useNavigate();
  const { id: electionId = "" } = useParams<{ id: string }>();
  const location = useLocation() as { state?: { electionName?: string } };
  const name = location?.state?.electionName ?? "Election";

  const [sending, setSending] = useState(false);

  async function sendAckAndExit() {
    try {
      setSending(true);
      await fetch("/voter/email-ack", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ election_id: electionId, election_name: name }),
      });
    } catch {
      // ignore; we’ll still route back to keep UX smooth
    } finally {
      nav("/voter");
    }
  }

  async function downloadReceipt() {
  try {
    const r = await fetch(`/voter/receipt?election_name=${encodeURIComponent(name)}`, {
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
    // Optional: infer filename from Content-Disposition header if present
    a.download = "vote_receipt.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    // Navigate away after starting the download
    nav("/voter");
  } catch {
    alert("Download failed.");
  }
}

  return (
    <div className="voter-landing">
      <main className="vl-main">
        <section className="vl-left">
          {/* Centered header */}
          <div className="vl-header-row" style={{ justifyContent: "center" }}>
            <h2 style={{ margin: 0, textAlign: "center" }}>{name}</h2>
          </div>

          {/* Bigger, centered card */}
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

            {/* Bigger GIF, centered */}
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

            {/* Evenly spaced buttons */}
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
                onClick={() => nav("/voter")}
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
