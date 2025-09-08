// services/api.ts

export class ApiRateLimitError extends Error {
  code = 'RATE_LIMIT' as const;
  retryAfter?: number;
  constructor(message = 'Too many requests', retryAfter?: number) {
    super(message);
    this.retryAfter = retryAfter;
  }
}

type JsonInit = Omit<RequestInit, 'headers' | 'body'> & {
  headers?: Record<string, string>;
  body?: any;                // string | FormData | Blob | ...
  timeoutMs?: number;        // per-call timeout (ms), default 10s
  expectJson?: boolean;      // defaults true
};

function fetchWithTimeout(input: RequestInfo | URL, init: RequestInit = {}, ms = 10000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), ms);
  const merged: RequestInit = {
    credentials: 'include',
    mode: 'cors',
    ...init,
    signal: init.signal ?? controller.signal,
  };
  return fetch(input, merged)
    .finally(() => clearTimeout(id));
}

/** Parse Retry-After header → seconds (int), or undefined */
function parseRetryAfter(h: string | null): number | undefined {
  if (!h) return;
  const n = Number(h);
  if (Number.isFinite(n)) return Math.max(0, Math.floor(n));
  // (date format variant not needed for our use; add if you want)
  return;
}

/** Core JSON helper with 429 + timeout handling */
export async function apiJson<T = any>(url: string, init: JsonInit = {}): Promise<T> {
  const {
    headers = {},
    body,
    timeoutMs = 10000,
    expectJson = true,
    ...rest
  } = init;

  // Only set JSON content-type when body is not FormData/Blob
  const isFormData = (typeof FormData !== 'undefined') && body instanceof FormData;
  const finalHeaders: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...headers,
  };

  let res: Response;
  try {
    res = await fetchWithTimeout(url, { ...rest, headers: finalHeaders, body }, timeoutMs);
  } catch (e: any) {
    if (e?.name === 'AbortError') throw new Error('Request timed out. Please try again.');
    throw new Error('Something went wrong. Please try again later.');
  }

  // Handle 429 early with Retry-After
  if (res.status === 429) {
    const retryAfter = parseRetryAfter(res.headers.get('Retry-After'));
    throw new ApiRateLimitError('Too many requests', retryAfter);
  }

  // Try to parse response body
  const contentType = res.headers.get('content-type') || '';
  const looksJson = contentType.includes('application/json');

  let parsed: any = null;
  if (expectJson) {
    if (!looksJson) {
      // non-JSON error bodies: read text for context
      const text = await res.text().catch(() => '');
      if (!res.ok) {
        const msg =
          res.status === 401 || res.status === 403
            ? 'Not authorized. Please log in again.'
            : `Unexpected response (${res.status}). ${text.slice(0, 180)}`;
        const err: any = new Error(msg);
        err._raw = text;
        err.status = res.status;
        throw err;
      }
      // ok but not JSON: return empty object
      return {} as T;
    }
    parsed = await res.json().catch(() => ({}));
  } else {
    // caller doesn’t expect JSON; just succeed/fail
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      const err: any = new Error(text || res.statusText || `HTTP ${res.status}`);
      err.status = res.status;
      err._raw = text;
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
    err._data = parsed;
    err.status = res.status;
    throw err;
  }

  return parsed as T;
}

/** Small helpers built atop apiJson */

type Opts = { signal?: AbortSignal; timeoutMs?: number };

export async function apiGet<T>(url: string, opts: Opts = {}): Promise<T> {
  return apiJson<T>(url, { method: 'GET', ...opts });
}

export async function apiDownload(url: string, filename?: string, opts: Opts = {}) {
  const { timeoutMs = 20000, signal } = opts;
  let res: Response;
  try {
    res = await fetchWithTimeout(url, { credentials: 'include', mode: 'cors', signal }, timeoutMs);
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
  a.href = urlObj;
  a.download = finalName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(urlObj);
}
