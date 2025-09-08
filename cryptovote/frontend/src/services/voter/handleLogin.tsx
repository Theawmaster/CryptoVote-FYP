import { apiJson } from '../api';
import { getFromIndexedDB } from '../../utils/indexeddb-utils';
import { openPassphraseModal } from '../../components/auth/PassphraseModal';
import { pickPrivateKeyFile } from '../../components/auth/pickPrivateKeyFile';
import {
  decryptPrivateKey,
  importPrivateKeyFromPEM,
  signNonce,
} from '../../utils/crypto-utils';

const LOGIN_URL = '/login';

type Toast = (type: 'success' | 'error' | 'info', msg: string) => void;

export async function handleLogin(
  email: string,
  showToast: Toast,
  setOtpStage: (v: boolean) => void,
  signal?: AbortSignal
) {
  if (!email.trim()) {
    showToast('error', 'Please enter your NTU email.');
    return;
  }

  // 1) Request nonce
  const { nonce } = await apiJson(LOGIN_URL, {
    method: 'POST',
    body: JSON.stringify({ email }),
    signal,
  });

  // 2) Load key (encrypted in IndexedDB or upload)
  let privateKey: CryptoKey | null = null;
  const encryptedKey = await getFromIndexedDB('cryptoVoteKeys', 'encryptedPrivateKey');

  if (encryptedKey) {
    showToast('info', 'Found encrypted key. Enter your passphrase.');
    const pass = await openPassphraseModal({ onCancel: async () => showToast('error', 'Cancelled.'), mode: 'get' });
    if (!pass) return;
    const pem = await decryptPrivateKey(encryptedKey, pass);
    privateKey = await importPrivateKeyFromPEM(pem);
  } else {
    showToast('info', 'No saved key. Please upload your private key (.pem).');
    const pem = await pickPrivateKeyFile();
    privateKey = await importPrivateKeyFromPEM(pem);
  }

  if (!privateKey) {
    showToast('error', 'Private key unavailable.');
    return;
  }

  // 3) Sign nonce
  const signed_nonce = await signNonce(privateKey, nonce);

  // 4) Verify signature (server sets session)
  await apiJson(LOGIN_URL, {
    method: 'POST',
    body: JSON.stringify({ email, signed_nonce }),
    signal,
  });
  setOtpStage(true);
  showToast('success', 'Signature verified. Please enter OTP.');
}
