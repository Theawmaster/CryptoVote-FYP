import React from 'react';
import type { ElectionStatus } from '../../services/admin/types';
import { fmtTime, prettyState } from '../../utils/format';

function KV({ k, v }: { k: string; v: React.ReactNode }) {
  return <div><dt>{k}</dt><dd>{v}</dd></div>;
}

export default function StatusPanel({ s, electionId, onClose }:{
  s: ElectionStatus; electionId: string; onClose: ()=>void;
}) {
  return (
    <div className="mgr-panel" role="region" aria-label="Election Status">
      <div className="mgr-panel__head">
        <div>Election Status</div>
        <button className="mgr-panel__close" onClick={onClose} aria-label="Close status panel">×</button>
      </div>

      <dl className="mgr-kv">
        <KV k="Election" v={s.name ?? '—'} />
        <KV k="State" v={prettyState(s)} />
        <KV k="Has started" v={String(!!s.has_started)} />
        <KV k="Has ended" v={String(!!s.has_ended)} />
        <KV k="Start time" v={fmtTime(s.start_time)} />
        <KV k="End time" v={fmtTime(s.end_time)} />
        <KV k="Tally generated" v={String(!!s.tally_generated)} />
        <KV k="ID" v={s.id ?? electionId} />
        <KV k="Candidate count" v={s.candidate_count ?? 0} />
        <KV k="Total votes" v={s.vote_count ?? 0} />
      </dl>
    </div>
  );
}
