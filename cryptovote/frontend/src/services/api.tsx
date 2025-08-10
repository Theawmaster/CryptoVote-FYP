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
  