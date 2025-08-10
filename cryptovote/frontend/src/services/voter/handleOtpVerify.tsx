import { apiJson } from '../api';

const OTP_URL = '/2fa-verify';

type Toast = (type: 'success' | 'error' | 'info', msg: string) => void;

export async function handleOtpVerify(
  email: string,
  otp: string,
  showToast: Toast,
  onSuccess?: () => void,
  signal?: AbortSignal
) {
  if (!otp.trim()) {
    showToast('error', 'Please enter OTP.');
    return;
  }

  await apiJson(OTP_URL, {
    method: 'POST',
    body: JSON.stringify({ email, otp }),
    signal,
  });

  showToast('success', '2FA successful. Access granted.');
  onSuccess?.();
}
