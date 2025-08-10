import { getFromIndexedDB } from '../../utils/indexeddb-utils';
import { decryptPrivateKey, importPrivateKeyFromPEM, signNonce } from '../../utils/crypto-utils';
import { pickPrivateKeyFile } from '../../components/auth/pickPrivateKeyFile';
import { openPassphraseModal } from '../../components/auth/PassphraseModal';

const LOGIN_URL = '/admin-login';

export async function handleLogin(
  email: string,
  showToast: (type: 'success' | 'error' | 'info', msg: string) => void,
  setOtpStage: (v: boolean) => void
) {
  if (!email.trim()) {
    showToast('error', 'Please enter your NTU email.');
    return;
  }
  if (!email.toLowerCase().includes('admin')) {
    showToast('error', 'This login is for admin accounts only.');
    return;
  }

  try {
    // Step 1: Request nonce
    const nonceRes = await fetch(LOGIN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email }),
    });
    const nonceData = await nonceRes.json();

    if (!nonceRes.ok || !nonceData?.nonce) {
      showToast('error', nonceData?.error || 'Unable to request nonce.');
      return;
    }

    // Step 2: Load private key
    let privateKey: CryptoKey | null = null;
    const encryptedKey = await getFromIndexedDB('cryptoVoteKeys', 'encryptedPrivateKey');

    if (encryptedKey) {
      showToast('info', 'Found encrypted key. Please enter your passphrase.');
      const passphrase = await openPassphraseModal({
        onCancel: async () => showToast('error', 'Cancelled.'),
        mode: 'get',
      });
      if (!passphrase) return;
      try {
        const decryptedPem = await decryptPrivateKey(encryptedKey, passphrase);
        privateKey = await importPrivateKeyFromPEM(decryptedPem);
      } catch {
        showToast('error', 'Incorrect passphrase or corrupt key.');
        return;
      }
    } else {
      showToast('info', 'No saved key. Please upload your private key.');
      try {
        const pem = await pickPrivateKeyFile();
        privateKey = await importPrivateKeyFromPEM(pem);
      } catch (err) {
        showToast('error', String(err));
        return;
      }
    }

    if (!privateKey) {
      showToast('error', 'Private key unavailable.');
      return;
    }

    // Step 3: Sign nonce
    const signedNonce = await signNonce(privateKey, nonceData.nonce);

    // Step 4: Send signed nonce
    const loginRes = await fetch(LOGIN_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, signed_nonce: signedNonce }),
    });
    const loginData = await loginRes.json();

    if (!loginRes.ok) {
      showToast('error', loginData?.error || 'Login failed.');
      return;
    }

    showToast('success', 'Signature verified. Please enter OTP.');
    setOtpStage(true);
  } catch (err) {
    console.error(err);
    showToast('error', 'Unexpected error during login.');
  }
}
