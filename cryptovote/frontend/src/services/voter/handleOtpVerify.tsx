// services/voter/handleOtpVerify.ts
import { apiJson, ApiRateLimitError } from '../api';

const OTP_URL = '/2fa-verify'; // ← match your Flask route

type Toast = (type: 'success' | 'error' | 'info', msg: string) => void;

export async function handleOtpVerify(
  email: string,
  otp: string,
  showToast: Toast,
  onSuccess?: () => void,
  signal?: AbortSignal
) {
  const code = (otp || '').trim();
  if (!code) {
    showToast('error', 'Please enter OTP.');
    return;
  }

  try {
    await apiJson(OTP_URL, {
      method: 'POST',
      body: JSON.stringify({ email, otp: code }),
      signal,
      timeoutMs: 8000,
    });

    showToast('success', '2FA successful. Access granted.');
    onSuccess?.();
  } catch (e: any) {
    if (e instanceof ApiRateLimitError) {
      const err: any = new Error(e.message);
      err.code = e.code;
      err.retryAfter = e.retryAfter ?? 5;
      throw err;
    }
    throw e; // component shows default error
  }
}
