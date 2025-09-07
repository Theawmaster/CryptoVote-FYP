// src/services/voter/http.ts
export async function safeJson<T = any>(res: Response): Promise<T | {}> {
  try { return await res.json(); } catch { return {}; }
}

export async function getJSON<T = any>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: 'include' });
  const body: any = await safeJson(res);
  if (!res.ok) throw new Error(body?.error || `HTTP ${res.status}`);
  return body as T;
}

export async function postJSON<T = any>(url: string, data: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const body: any = await safeJson(res);
  if (!res.ok) throw new Error(body?.error || `HTTP ${res.status}`);
  return body as T;
}

export async function downloadJson(url: string, filename: string): Promise<void> {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) {
    const j = await safeJson(res as any);
    const msg = (j as any)?.error || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  let blob: Blob;
  try {
    const j = await res.clone().json();
    blob = new Blob([JSON.stringify(j, null, 2)], { type: 'application/json' });
  } catch {
    blob = await res.blob();
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
