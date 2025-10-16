// services/api.ts

// ---------- Base URL detection + joiner ----------
const ENV_BASE =
  // Vite
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_BASE) ||
  // CRA / Next
  (typeof process !== 'undefined' &&
    ((process.env as any).REACT_APP_API_BASE || (process.env as any).NEXT_PUBLIC_API_BASE)) ||
  undefined;

const detectApiBase = () => {
  
  if (ENV_BASE) return ENV_BASE as string;

  const { protocol, hostname, port } = window.location;
  const isLocal = ['localhost', '127.0.0.1', '::1', '0.0.0.0'].includes(hostname);
  const isDevPort = ['3000', '5173', '5174'].includes(port || '');

  // FE dev → talk to BE on :5010
  if (isLocal && isDevPort) return `${protocol}//${hostname}:5010`;

  // Otherwise same-origin (prod/preview)
  return `${protocol}//${hostname}${port ? ':' + port : ''}`;
};

const API_BASE = detectApiBase();


const ABS = /^https?:\/\//i;
const joinUrl = (u: string) => (ABS.test(u) ? u : `${API_BASE}/${u.replace(/^\/+/, '')}`);
// console.log('API_BASE =', API_BASE); // uncomment to verify

// ---------- Errors ----------
export class ApiRateLimitError extends Error {
  code = 'RATE_LIMIT' as const;
  retryAfter?: number;
  constructor(message = 'Too many requests', retryAfter?: number) {
    super(message);
    this.retryAfter = retryAfter;
  }
}

// ---------- Types ----------
export type JsonInit = Omit<RequestInit, 'headers' | 'body'> & {
  headers?: Record<string, string>;
  body?: any;          // string | FormData | Blob | ...
  timeoutMs?: number;  // per-call timeout (ms), default 10s
  expectJson?: boolean; // defaults true
};

type Opts = { signal?: AbortSignal; timeoutMs?: number };

// ---------- Internals ----------
function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, ms = 10000) {
  const timeoutController = new AbortController();
  let timedOut = false;
  const id = setTimeout(() => { timedOut = true; timeoutController.abort(); }, ms);

  const callerSignal = (init as any).signal as AbortSignal | undefined;
  if (callerSignal) {
    // Clear our timeout if caller cancels first
    const onCallerAbort = () => clearTimeout(id);
    if (callerSignal.aborted) clearTimeout(id);
    else callerSignal.addEventListener('abort', onCallerAbort, { once: true });
  }

  const merged: RequestInit = {
    credentials: 'include',
    mode: 'cors',
    ...init,
    signal: callerSignal ?? timeoutController.signal,
  };

  return fetch(input, merged)
    .finally(() => clearTimeout(id))
    .catch((e: any) => {
      if (e?.name === 'AbortError') {
        // annotate the error so callers know *why* it aborted
        e._timeout = timedOut;
        e._cancelled = !timedOut && !!callerSignal?.aborted;
      }
      throw e;
    });
}

/** Parse Retry-After header → seconds (int), or undefined */
function parseRetryAfter(h: string | null): number | undefined {
  if (!h) return;
  const n = Number(h);
  if (Number.isFinite(n)) return Math.max(0, Math.floor(n));
  const d = Date.parse(h);
  if (!Number.isNaN(d)) {
    const secs = Math.ceil((d - Date.now()) / 1000);
    return secs > 0 ? secs : 0;
  }
}

// ---------- Public API ----------
export async function apiJson<T = any>(url: string, init: JsonInit = {}): Promise<T> {
  const {
    headers = {},
    body,
    timeoutMs = 10000,
    expectJson = true,
    ...rest
  } = init;

  const isFormData = (typeof FormData !== 'undefined') && body instanceof FormData;
  const isBlob     = (typeof Blob !== 'undefined') && body instanceof Blob;

  // ✅ only set JSON header when we truly send a JSON body
  const method = (rest.method ?? 'GET').toString().toUpperCase();
  const hasJsonBody = !isFormData && !isBlob && body != null && method !== 'GET';

  const finalHeaders: Record<string, string> = {
    ...(hasJsonBody ? { 'Content-Type': 'application/json' } : {}),
    ...headers,
  };

  const finalBody =
    isFormData || isBlob || typeof body === 'string' || body == null
      ? body
      : JSON.stringify(body);

  let res: Response;
  try {
    // IMPORTANT: uses joinUrl so '/admin/...' → 'http://localhost:5010/admin/...'
    res = await fetchWithTimeout(
      joinUrl(url),
      { ...rest, headers: finalHeaders, body: finalBody },
      timeoutMs
    );
  } catch (e: any) {
    if (e?.name === 'AbortError') {
      if (e._cancelled) {
        const err: any = new Error('Request cancelled.');
        err.code = 'CANCELLED';
        throw err;
      }
      if (e._timeout) {
        const err: any = new Error('Request timed out. Please try again.');
        err.code = 'TIMEOUT';
        throw err;
      }
      const err: any = new Error('Request aborted.');
      err.code = 'ABORTED';
      throw err;
    }
    throw new Error('Something went wrong. Please try again later.');
  }

  if (res.status === 429) {
    const retryAfter = parseRetryAfter(res.headers.get('Retry-After'));
    throw new ApiRateLimitError('Too many requests', retryAfter);
  }

  const contentType = res.headers.get('content-type') || '';
  const looksJson = contentType.includes('application/json');

  if (!expectJson) {
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      const err: any = new Error(text || res.statusText || `HTTP ${res.status}`);
      err.status = res.status; err._raw = text;
      throw err;
    }
    return {} as T;
  }

  let parsed: any = null;
  if (looksJson) {
    parsed = await res.json().catch(() => ({}));
  } else {
    const text = await res.text().catch(() => '');
    if (!res.ok) {
      const msg =
        res.status === 401 || res.status === 403
          ? 'Not authorized. Please log in again.'
          : `Unexpected response (${res.status}). ${text.slice(0, 180)}`;
      const err: any = new Error(msg);
      err._raw = text; err.status = res.status;
      throw err;
    }
    return {} as T;
  }

  if (!res.ok) {
    const msg =
      (parsed && (parsed.error || parsed.message)) ||
      (res.status === 401 || res.status === 403
        ? 'Not authorized. Please log in again.'
        : `Request failed (${res.status})`);
    const err: any = new Error(msg);
    err._data = parsed; err.status = res.status;
    throw err;
  }

  return parsed as T;
}

export async function apiGet<T>(url: string, opts: Opts = {}): Promise<T> {
  return apiJson<T>(url, { method: 'GET', ...opts });
}

export async function apiDownload(url: string, filename?: string, opts: Opts = {}) {
  const { timeoutMs = 20000, signal } = opts;
  let res: Response;
  try {
    // 👇 IMPORTANT: use joinUrl here too
    res = await fetchWithTimeout(joinUrl(url), { credentials: 'include', mode: 'cors', signal }, timeoutMs);
  } catch (e: any) {
    if (e?.name === 'AbortError') throw new Error('Download timed out. Please try again.');
    throw new Error('Network error during download.');
  }

  if (res.status === 429) {
    const retryAfter = parseRetryAfter(res.headers.get('Retry-After'));
    throw new ApiRateLimitError('Too many requests', retryAfter);
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || res.statusText || `HTTP ${res.status}`);
  }

  // prefer server filename if provided
  const cd = res.headers.get('content-disposition') || '';
  const nameFromServer = /filename\*=UTF-8''([^;]+)|filename="([^"]+)"/i.exec(cd);
  const finalName = decodeURIComponent(nameFromServer?.[1] || nameFromServer?.[2] || filename || 'download');

  const blob = await res.blob();
  const a = document.createElement('a');
  const urlObj = URL.createObjectURL(blob);
  a.href = urlObj; a.download = finalName;
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(urlObj);
}
