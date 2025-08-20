export async function apiJson(
    url: string,
    init: RequestInit & { signal?: AbortSignal } = {}
  ) {
    const res = await fetch(url, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(init.headers || {}) },
      ...init,
    });
  
    const ct = res.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      const text = await res.text().catch(() => '');
      const err = new Error(
        res.status === 401 || res.status === 403
          ? 'Not authorized. Please log in again.'
          : `Non-JSON response (${res.status}). ${text.slice(0, 180)}`
      );
      (err as any)._raw = text;
      throw err;
    }
  
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(data?.error || `Request failed (${res.status})`);
      (err as any)._data = data;
      throw err;
    }
    return data;
  }

  type Opts = { signal?: AbortSignal };

async function parseErr(res: Response) {
  try { const j = await res.json(); return j?.error || res.statusText; }
  catch { return res.statusText; }
}

export async function apiGet<T>(url: string, opts: Opts = {}): Promise<T> {
  const res = await fetch(url, { credentials: 'include', signal: opts.signal });
  if (!res.ok) throw new Error(await parseErr(res));
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) throw new Error(`Unexpected content-type: ${ct}`);
  return res.json() as Promise<T>;
}

export async function apiDownload(url: string, filename: string) {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) throw new Error(await parseErr(res));
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}
