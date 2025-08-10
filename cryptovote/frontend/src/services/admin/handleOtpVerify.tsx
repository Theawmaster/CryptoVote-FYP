const OTP_URL = '/2fa-verify';

export async function handleOtpVerify(
  email: string,
  otp: string,
  showToast: (type: 'success' | 'error' | 'info', msg: string) => void,
  navigate: (path: string, options?: any) => void
) {
  if (!otp.trim()) {
    showToast('error', 'Please enter OTP.');
    return;
  }

  try {
    const otpRes = await fetch(OTP_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, otp }),
    });
    const otpData = await otpRes.json();

    if (!otpRes.ok) {
      showToast('error', otpData?.error || 'OTP verification failed.');
      return;
    }

    if (otpData.role !== 'admin') {
      showToast('error', 'Access denied. You are not an admin.');
      return;
    }

    showToast('success', '2FA successful. Access granted.');
    navigate('/admin/landing', { replace: true, state: { email } });
  } catch {
    showToast('error', 'Unexpected error during OTP verification.');
  }
}
