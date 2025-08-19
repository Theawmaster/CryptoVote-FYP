// Election-related API calls
async function mustJson(res: Response) {
    const ct = res.headers.get('content-type') || '';
    const data = ct.includes('application/json') ? await res.json() : {};
    if (!res.ok) {
      const msg = (data as any)?.error || `Request failed (${res.status})`;
      const err = new Error(msg) as any;
      err._data = data;
      throw err;
    }
    return data;
  }

  // Get election status
  export async function getElectionStatus(id: string) {
    const res = await fetch(`/admin/election-status/${encodeURIComponent(id)}`, {
      method: 'GET',
      credentials: 'include',
    });
    return mustJson(res);
  }

  // Start election
  export async function startElection(id: string) {
    const res = await fetch(`/admin/start-election/${encodeURIComponent(id)}`, {
      method: 'POST',
      credentials: 'include',
    });
    return mustJson(res);
  }

  // End election
  export async function endElection(id: string) {
    const res = await fetch(`/admin/end-election/${encodeURIComponent(id)}`, {
      method: 'POST',
      credentials: 'include',
    });
    return mustJson(res);
  }

  // Tally election
  export async function tallyElection(electionId: string) {
    const res = await fetch(`/admin/tally-election/${encodeURIComponent(electionId)}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || 'Failed to tally');
    return data as {
      message: string;
      election_id: string;
      tally: Array<{candidate_id: string; vote_count: number | string}>;
      zkp_proofs?: any[];
    };
  }

  // Download election report
  export async function downloadReportFile(electionId: string, format: 'pdf'|'csv' = 'pdf') {
    const res = await fetch(`/admin/download-report/${encodeURIComponent(electionId)}?format=${format}`, {
      method: 'GET',
      credentials: 'include',
    });
    if (!res.ok) {
      let msg = 'Failed to download report';
      try { const j = await res.json(); msg = j?.error || msg; } catch {}
      throw new Error(msg);
    }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    const stamp = new Date().toISOString().slice(0,19).replace(/[:T]/g,'-');
    a.href = url;
    a.download = `cryptovote-${electionId}-report-${stamp}.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }
    