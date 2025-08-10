import { apiJson } from '../api';

const REGISTER_URL = '/register/';

export async function requestRegistration(
  email: string,
  signal?: AbortSignal
): Promise<{ message?: string; private_key?: string | null }> {
  const normalized = email.trim().toLowerCase();
  return apiJson(REGISTER_URL, {
    method: 'POST',
    body: JSON.stringify({ email: normalized, vote_role: 'voter' }),
    signal,
  });
}

export async function cancelRegistration(email: string) {
  try {
    await apiJson(`${REGISTER_URL}cancel`, {
      method: 'POST',
      body: JSON.stringify({ email: email.trim().toLowerCase() }),
    });
  } catch {
    // swallow — best-effort cancel
  }
}
