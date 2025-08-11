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

const CreateElectionForm: React.FC<Props> = ({ onCreated }) => {
  const [electionId, setElectionId] = useState('');
  const [electionName, setElectionName] = useState('');

  type Row = { name: string; id: string; touched?: boolean };
  const [rows, setRows] = useState<Row[]>([{ name: '', id: '' }]); // start with one blank

  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  // derive ids from names when user hasn't typed a custom id
  const normalizedRows = useMemo(() => {
    return rows.map(r => {
      const auto = slugify(r.name);
      return { ...r, id: r.id || auto };
    });
  }, [rows]);

  const addRow = () => setRows(prev => [...prev, { name: '', id: '' }]);
  const removeRow = (idx: number) =>
    setRows(prev => prev.filter((_, i) => i !== idx));

  const updateName = (idx: number, name: string) =>
    setRows(prev => prev.map((r, i) => (i === idx ? { ...r, name, touched: r.touched } : r)));

  const updateId = (idx: number, id: string) =>
    setRows(prev => prev.map((r, i) => (i === idx ? { ...r, id, touched: true } : r)));

  const handleCreate = async () => {
    setErr(null);
    setOk(null);

    const id = electionId.trim();
    const name = electionName.trim();

    if (!id || !name) {
      setErr('Please fill in both Election ID and Election Name.');
      return;
    }
    if (!/^[a-z0-9_-]+$/i.test(id)) {
      setErr('Election ID can only contain letters, numbers, underscores, and hyphens.');
      return;
    }

    // Prepare candidates: keep only rows with a non-empty name
    const candidates = normalizedRows
      .map(r => ({ id: slugify(r.id || r.name), name: r.name.trim() }))
      .filter(r => r.name.length > 0);

    // Optional validation: enforce unique candidate IDs & names
    const ids = new Set<string>();
    for (const c of candidates) {
      if (!/^[a-z0-9_-]+$/i.test(c.id)) {
        setErr(`Candidate ID "${c.id}" is invalid. Use letters, numbers, "_" or "-".`);
        return;
      }
      if (ids.has(c.id)) {
        setErr(`Duplicate candidate ID detected: "${c.id}".`);
        return;
      }
      ids.add(c.id);
    }

    setSubmitting(true);
    try {
      const res = await fetch('/admin/create-election', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ id, name, candidates }),
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
      setRows([{ name: '', id: '' }]);

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
          />
          <div className="hint">Unique. Letters, numbers, “_” or “-”.</div>
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
          />
          <div className="hint">&nbsp;</div>
        </div>

        <div className="actions">
          <button className="btn-primary" onClick={handleCreate} disabled={submitting}>
            {submitting ? 'Creating…' : '+ Create New'}
          </button>
        </div>
      </div>

      {/* Candidates */}
      <div className="cand-header">Candidates (optional)</div>

      <div className="cand-list">
        {normalizedRows.map((r, idx) => (
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
              />
            </div>

            <div className="field">
              <label htmlFor={`cand-id-${idx}`}>Candidate ID</label>
              <input
                id={`cand-id-${idx}`}
                type="text"
                placeholder="auto-from-name"
                value={rows[idx].touched ? rows[idx].id : r.id}
                onChange={(e) => updateId(idx, e.target.value)}
                disabled={submitting}
                autoComplete="off"
              />
              <div className="hint">Auto-fills from name; you can edit.</div>
            </div>

            <div className="cand-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => removeRow(idx)}
                disabled={submitting || rows.length === 1}
                title={rows.length === 1 ? 'Keep at least one row' : 'Remove candidate'}
              >
                Remove
              </button>
            </div>
          </div>
        ))}
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
