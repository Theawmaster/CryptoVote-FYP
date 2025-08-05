// src/utils/crypto-utils.ts
// Utility functions for key encryption, PEM downloads, and optional WebAuthn protection.

export async function encryptPrivateKey(privateKeyPem: string, passphrase: string) {
    const enc = new TextEncoder();
  
    // Derive AES key from passphrase
    const passphraseKey = await crypto.subtle.importKey(
      'raw',
      enc.encode(passphrase),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
  
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const aesKey = await crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt, iterations: 100_000, hash: 'SHA-256' },
      passphraseKey,
      { name: 'AES-GCM', length: 256 },
      true, // extractable so we can wrap if needed
      ['encrypt', 'decrypt']
    );
  
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      aesKey,
      enc.encode(privateKeyPem)
    );
  
    return {
      salt: Array.from(salt),
      iv: Array.from(iv),
      ciphertext: Array.from(new Uint8Array(ciphertext)),
      aesKey, // return raw key handle for optional wrapping
    };
  }
  
  export async function decryptPrivateKey(encryptedData: {
    salt: number[];
    iv: number[];
    ciphertext: number[];
  }, passphrase: string) {
    const enc = new TextEncoder();
    const dec = new TextDecoder();
  
    const passphraseKey = await crypto.subtle.importKey(
      'raw',
      enc.encode(passphrase),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );
  
    const aesKey = await crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt: new Uint8Array(encryptedData.salt), iterations: 100_000, hash: 'SHA-256' },
      passphraseKey,
      { name: 'AES-GCM', length: 256 },
      false,
      ['decrypt']
    );
  
    const plaintext = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: new Uint8Array(encryptedData.iv) },
      aesKey,
      new Uint8Array(encryptedData.ciphertext)
    );
  
    return dec.decode(plaintext);
  }
  
  export function downloadPem(privateKeyPem: string, filename = 'cryptovote-private-key.pem') {
    const blob = new Blob([privateKeyPem], { type: 'application/x-pem-file' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }
  
  /* ------------------ WebAuthn Wrapping ------------------ */
  
  /**
   * Wrap AES key with a hardware-bound WebAuthn credential.
   */
  export async function wrapKeyWithWebAuthn(aesKey: CryptoKey) {
    if (!window.PublicKeyCredential) {
      throw new Error('WebAuthn not supported in this browser.');
    }
  
    const publicKeyOptions: PublicKeyCredentialCreationOptions = {
      challenge: crypto.getRandomValues(new Uint8Array(32)),
      rp: { name: 'CryptoVote' },
      user: {
        id: crypto.getRandomValues(new Uint8Array(16)),
        name: 'cryptovote-user',
        displayName: 'CryptoVote User',
      },
      pubKeyCredParams: [{ type: 'public-key', alg: -7 }], // ES256
      authenticatorSelection: { userVerification: 'required' },
      timeout: 60000,
      attestation: 'direct',
    };
  
    const credential = (await navigator.credentials.create({ publicKey: publicKeyOptions })) as PublicKeyCredential;
    if (!credential) throw new Error('WebAuthn credential creation failed.');
  
    // Export AES key as raw bytes
    const rawAesKey = await crypto.subtle.exportKey('raw', aesKey);
  
    // For demo purposes, we'll store WebAuthn credential + encrypted AES key together
    // In a real system, you'd use WebAuthn to sign a challenge that unlocks the AES key server-side
    return {
      credentialId: arrayBufferToBase64(credential.rawId),
      wrappedKey: arrayBufferToBase64(rawAesKey),
    };
  }
  
  export async function unwrapKeyWithWebAuthn(credentialId: string, wrappedKeyBase64: string) {
    if (!window.PublicKeyCredential) {
      throw new Error('WebAuthn not supported in this browser.');
    }
  
    const publicKeyRequestOptions: PublicKeyCredentialRequestOptions = {
      challenge: crypto.getRandomValues(new Uint8Array(32)),
      allowCredentials: [
        {
          type: 'public-key',
          id: base64ToArrayBuffer(credentialId),
        },
      ],
      userVerification: 'required',
      timeout: 60000,
    };
  
    const assertion = (await navigator.credentials.get({ publicKey: publicKeyRequestOptions })) as PublicKeyCredential;
    if (!assertion) throw new Error('WebAuthn authentication failed.');
  
    // In a real design, assertion.signature would be verified server-side before unwrapping
    const rawKeyBytes = base64ToArrayBuffer(wrappedKeyBase64);
    return await crypto.subtle.importKey('raw', rawKeyBytes, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
  }
  
  /* ------------------ Helpers ------------------ */
  function arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    bytes.forEach(b => binary += String.fromCharCode(b));
    return btoa(binary);
  }
  
  function base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes.buffer;
  }

  /*   * Import a PEM-encoded private key into a CryptoKey object. */
  
  export async function importPrivateKeyFromPEM(pem: string): Promise<CryptoKey> {
    const b64 = pem.replace(/-----[^-]+-----/g, '').replace(/\s+/g, '');
    const binary = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    return crypto.subtle.importKey(
      'pkcs8',
      binary.buffer,
      { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
      false,
      ['sign']
    );
  }
  
  export async function signNonce(privateKey: CryptoKey, nonce: string) {
    const signature = await crypto.subtle.sign(
      'RSASSA-PKCS1-v1_5',
      privateKey,
      new TextEncoder().encode(nonce)
    );
    return btoa(String.fromCharCode(...Array.from(new Uint8Array(signature))));
  }