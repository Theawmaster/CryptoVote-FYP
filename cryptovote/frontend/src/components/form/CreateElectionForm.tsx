import React, { useMemo, useState } from 'react';

type ElectionDTO = {
  id: string;
  name: string;
  start_time: string | null;
  end_time: string | null;
  is_active: boolean;
  has_started: boolean;
  has_ended: boolean;
  tally_generated: boolean;
  candidates?: { id: string; name: string }[];
};

type Props = { onCreated?: (e: ElectionDTO) => void };

// ---------- config ----------
const ID_RE = /^[A-Za-z0-9_-]{3,64}$/;     // for election + candidate ids
const NAME_MAX = 100;
const MIN_CANDIDATES = 2;

// simple slugify for candidate id from name
function slugify(s: string) {
  return s
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\s_-]/g, '')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .slice(0, 64);
}

type Row = { name: string; id: string; touched?: boolean };

const CreateElectionForm: React.FC<Props> = ({ onCreated }) => {
  const [electionId, setElectionId] = useState('');
  const [electionName, setElectionName] = useState('');

  // start with MIN_CANDIDATES blank rows
  const [rows, setRows] = useState<Row[]>(
    Array.from({ length: MIN_CANDIDATES }, () => ({ name: '', id: '' }))
  );

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  // derive ids from names when user hasn't typed a custom id
  const normalizedRows = useMemo(() => {
    return rows.map(r => {
      const auto = slugify(r.name);
      return { ...r, id: r.touched ? r.id : (r.id || auto) };
    });
  }, [rows]);

  const addRow = () => setRows(prev => [...prev, { name: '', id: '' }]);
  const removeRow = (idx: number) =>
    setRows(prev => (prev.length > MIN_CANDIDATES ? prev.filter((_, i) => i !== idx) : prev));

  const updateName = (idx: number, name: string) =>
    setRows(prev => prev.map((r, i) => (i === idx ? { ...r, name } : r)));

  const updateId = (idx: number, id: string) =>
    setRows(prev => prev.map((r, i) => (i === idx ? { ...r, id, touched: true } : r)));

  // -------- validation helpers --------
  type ValidState = {
    ok: boolean;
    message?: string;
    candidates?: { id: string; name: string }[];
    fieldErrors?: {
      electionId?: boolean;
      electionName?: boolean;
      candidate?: Record<number, { name?: boolean; id?: boolean }>;
    };
  };

  function validateAll(): ValidState {
    const fieldErrors: ValidState['fieldErrors'] = { candidate: {} };

    const id = electionId.trim();
    const name = electionName.trim();

    if (!ID_RE.test(id)) {
      fieldErrors.electionId = true;
      return { ok: false, message: 'Election ID must be 3–64 chars: letters, numbers, "_" or "-".', fieldErrors };
    }
    if (!name || name.length > NAME_MAX) {
      fieldErrors.electionName = true;
      return { ok: false, message: 'Election name is required.', fieldErrors };
    }

    // require every visible row to be filled (no half-empty rows)
    const filled = normalizedRows.map((r, i) => {
      const n = r.name.trim();
      const cid = (r.id || slugify(r.name)).trim();
      const thisErr: { name?: boolean; id?: boolean } = {};
      if (!n) thisErr.name = true;
      if (!ID_RE.test(cid)) thisErr.id = true;
      if (thisErr.name || thisErr.id) fieldErrors.candidate![i] = thisErr;
      return { name: n, id: cid };
    });

    // Must have at least MIN_CANDIDATES fully valid rows
    const validCands = filled.filter(c => c.name && ID_RE.test(c.id));
    if (validCands.length < MIN_CANDIDATES) {
      return { ok: false, message: `Please provide at least ${MIN_CANDIDATES} candidates (name + valid ID).`, fieldErrors };
    }

    // uniqueness of candidate IDs
    const seen = new Set<string>();
    for (let i = 0; i < filled.length; i++) {
      const c = filled[i];
      if (!c.name || !ID_RE.test(c.id)) continue;
      if (seen.has(c.id)) {
        fieldErrors.candidate![i] = { ...(fieldErrors.candidate![i] || {}), id: true };
        return { ok: false, message: `Duplicate candidate ID: "${c.id}".`, fieldErrors };
      }
      seen.add(c.id);
    }

    return { ok: true, candidates: validCands };
  }

  const canSubmit = useMemo(() => validateAll().ok, [electionId, electionName, normalizedRows]);

  // -------- submit --------
  const handleCreate = async () => {
    setErr(null);
    setOk(null);

    const v = validateAll();
    if (!v.ok) {
      setErr(v.message || 'Please fix the highlighted fields.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch('/admin/create-election', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          id: electionId.trim(),
          name: electionName.trim(),
          candidates: v.candidates, // already validated & trimmed
        }),
      });

      const ct = res.headers.get('content-type') || '';
      const data = ct.includes('application/json') ? await res.json() : {};

      if (!res.ok) {
        setErr((data as any)?.error || `Failed (${res.status})`);
        return;
      }

      setOk((data as any)?.message || 'Election created.');
      setElectionId('');
      setElectionName('');
      setRows(Array.from({ length: MIN_CANDIDATES }, () => ({ name: '', id: '' })));

      const created = (data as any)?.election as ElectionDTO | undefined;
      if (created && onCreated) onCreated(created);
    } catch (e: any) {
      setErr(e?.message || 'Network error while creating election.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section id="create-election-anchor" className="create-election-box">
      {/* Election basics */}
      <div className="create-row">
        <div className="field">
          <label htmlFor="election-id">Election ID</label>
          <input
            id="election-id"
            type="text"
            placeholder="e.g. election_2025"
            value={electionId}
            onChange={(e) => setElectionId(e.target.value)}
            disabled={submitting}
            autoComplete="off"
            inputMode="text"
            required
            aria-invalid={!ID_RE.test((electionId || '').trim())}
          />
          <div className="hint">Unique. 3–64 chars: letters, numbers, “_” or “-”.</div>
        </div>

        <div className="field">
          <label htmlFor="election-name">Election Name</label>
          <input
            id="election-name"
            type="text"
            placeholder="e.g. NTU CryptoVote Election 2025"
            value={electionName}
            onChange={(e) => setElectionName(e.target.value)}
            disabled={submitting}
            autoComplete="off"
            required
            aria-invalid={!electionName.trim()}
          />
          <div className="hint">&nbsp;</div>
        </div>

        <div className="actions">
          <button
            className="btn-primary"
            onClick={handleCreate}
            disabled={submitting || !canSubmit}
            title={!canSubmit ? 'Fill in all required fields' : undefined}
          >
            {submitting ? 'Creating…' : '+ Create New'}
          </button>
        </div>
      </div>

      {/* Candidates */}
      <div className="cand-header">Candidates <span className="muted">(at least {MIN_CANDIDATES})</span></div>

      <div className="cand-list">
        {normalizedRows.map((r, idx) => {
          const nameInvalid = !rows[idx].name.trim();
          const idValue = rows[idx].touched ? rows[idx].id : r.id;
          const idInvalid = !ID_RE.test((idValue || '').trim());
          return (
            <div className="cand-row" key={idx}>
              <div className="field">
                <label htmlFor={`cand-name-${idx}`}>Name</label>
                <input
                  id={`cand-name-${idx}`}
                  type="text"
                  placeholder="e.g. Alice Tan"
                  value={rows[idx].name}
                  onChange={(e) => updateName(idx, e.target.value)}
                  disabled={submitting}
                  autoComplete="off"
                  required
                  aria-invalid={nameInvalid}
                />
              </div>

              <div className="field">
                <label htmlFor={`cand-id-${idx}`}>Candidate ID</label>
                <input
                  id={`cand-id-${idx}`}
                  type="text"
                  placeholder="auto-from-name"
                  value={idValue}
                  onChange={(e) => updateId(idx, e.target.value)}
                  disabled={submitting}
                  autoComplete="off"
                  required
                  aria-invalid={idInvalid}
                />
                <div className="hint">Auto-fills from name; you can edit.</div>
              </div>

              <div className="cand-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => removeRow(idx)}
                  disabled={submitting || rows.length <= MIN_CANDIDATES}
                  title={rows.length <= MIN_CANDIDATES ? `Keep at least ${MIN_CANDIDATES}` : 'Remove candidate'}
                >
                  Remove
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="cand-footer">
        <button type="button" className="btn-secondary" onClick={addRow} disabled={submitting}>
          + Add candidate
        </button>
      </div>

      {err && <div className="form-message error">{err}</div>}
      {ok  && <div className="form-message success">{ok}</div>}
    </section>
  );
};

export default CreateElectionForm;
