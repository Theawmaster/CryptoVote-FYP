// src/components/voter/ElectionCard.tsx
import React from 'react';
import type { Election } from '../../services/voter/elections';

export default function ElectionCard({
  e, busy, onStart,
}: { e: Election; busy: boolean; onStart: (id: string) => void }) {
  return (
    <article className="vl-card">
      <div className="vl-card-title">{e.name}</div>
      <div className="vl-card-meta">
        <div>ID: {e.id}</div>
        <div>Starts: {e.start_time ? new Date(e.start_time).toLocaleString() : '—'}</div>
        <div>Ends: {e.end_time ? new Date(e.end_time).toLocaleString() : '—'}</div>
        <div>Candidates: {e.candidate_count ?? 0}</div>
      </div>
      <button
        className="vl-start"
        disabled={busy}
        onClick={() => onStart(e.id)}
        aria-label={`Start voting in ${e.name}`}
      >
        {busy ? 'Preparing…' : 'Start'}
      </button>
    </article>
  );
}
