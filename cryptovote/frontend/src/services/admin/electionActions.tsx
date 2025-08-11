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
  
  export async function getElectionStatus(id: string) {
    const res = await fetch(`/admin/election-status/${encodeURIComponent(id)}`, {
      method: 'GET',
      credentials: 'include',
    });
    return mustJson(res);
  }
  
  export async function startElection(id: string) {
    const res = await fetch(`/admin/start-election/${encodeURIComponent(id)}`, {
      method: 'POST',
      credentials: 'include',
    });
    return mustJson(res);
  }
  
  export async function endElection(id: string) {
    const res = await fetch(`/admin/end-election/${encodeURIComponent(id)}`, {
      method: 'POST',
      credentials: 'include',
    });
    return mustJson(res);
  }
  