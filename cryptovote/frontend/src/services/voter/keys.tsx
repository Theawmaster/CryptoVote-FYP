// src/services/keys.ts
import { getJSON } from './http';
import type { RsaPub } from '../../lib/cred';

export function normalizeRsaKey(raw: any): RsaPub {
  const key_id = raw?.key_id ?? raw?.id;
  const n_hex  = raw?.n_hex ?? raw?.nHex ?? raw?.n ?? raw?.modulusHex;
  const e_dec  = raw?.e_dec ?? raw?.eDec ?? (typeof raw?.e !== 'undefined' ? String(raw.e) : undefined);
  if (!key_id || !n_hex || !e_dec) throw new Error('Invalid RSA key format');
  return { key_id, n_hex, e_dec };
}

export async function getRsaPub(rsaKeyId: string): Promise<RsaPub> {
  const body: any = await getJSON('/public-keys');

  let candidates: any[] = [];
  if (Array.isArray(body?.rsa)) candidates = body.rsa;
  else if (body?.rsa && typeof body.rsa === 'object') candidates = [body.rsa];
  else if (body?.key_id || body?.nHex || body?.n_hex) candidates = [body];

  if (!candidates.length) throw new Error('No RSA keys available');

  const raw = candidates.find(k => (k?.key_id ?? k?.id) === rsaKeyId) ?? candidates[0];
  return normalizeRsaKey(raw);
}
