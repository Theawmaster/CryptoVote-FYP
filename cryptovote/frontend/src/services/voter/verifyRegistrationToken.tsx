import { apiJson } from '../api';

const VERIFY_URL = '/register/verify-email';

export async function verifyRegistrationToken(
  token: string,
  signal?: AbortSignal
): Promise<{ totp_uri: string; message?: string }> {
  const url = `${VERIFY_URL}?token=${encodeURIComponent(token.trim())}`;
  return apiJson(url, { method: 'GET', signal });
}
