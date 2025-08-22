export type RsaPub = { key_id: string; n_hex: string; e_dec: string };

// ---------- token ----------
export function genToken(): string {
  const bytes = new Uint8Array(32);            // 256-bit random
  crypto.getRandomValues(bytes);
  // base64url
  return btoa(String.fromCharCode(...Array.from(bytes)))
    .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/,"");
}

// ---------- bigint helpers ----------
function hexToBigInt(hex: string): bigint {
  const clean = hex.startsWith("0x") ? hex.slice(2) : hex;
  return BigInt("0x" + clean);
}
function bigIntToHex(n: bigint): string { return n.toString(16); }

function modPow(base: bigint, exp: bigint, mod: bigint): bigint {
  let res = 1n, b = base % mod, e = exp;
  while (e > 0n) {
    if (e & 1n) res = (res * b) % mod;
    b = (b * b) % mod;
    e >>= 1n;
  }
  return res;
}
function gcd(a: bigint, b: bigint): bigint {
  while (b !== 0n) [a, b] = [b, a % b];
  return a;
}
function egcd(a: bigint, b: bigint): [bigint, bigint, bigint] {
  if (a === 0n) return [b, 0n, 1n];
  const [g, x1, y1] = egcd(b % a, a);
  return [g, y1 - (b / a) * x1, x1];
}
function modInv(a: bigint, m: bigint): bigint {
  const [g, x] = egcd(a, m);
  if (g !== 1n) throw new Error("modular inverse does not exist");
  return (x % m + m) % m;
}
function randomCoprimeBelow(n: bigint): bigint {
  const bytes = Math.ceil(n.toString(16).length / 2);
  const buf = new Uint8Array(bytes);
  let r = 0n;
  do {
    crypto.getRandomValues(buf);
    let hex = "";
    for (const b of buf) hex += b.toString(16).padStart(2, "0");
    r = hexToBigInt(hex) % n;
  } while (r === 0n || gcd(r, n) !== 1n);
  return r;
}

// ---------- hashing (browser SubtleCrypto) ----------
async function sha256ToBigInt(inputUtf8: string): Promise<bigint> {
  const enc = new TextEncoder();
  const data = enc.encode(inputUtf8);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const hex = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
  return hexToBigInt(hex);
}

// ---------- core API (matches Python) ----------
// m = SHA256(token); blinded = (r^e mod n) * m mod n
export async function blindToken(
  token: string,
  pub: RsaPub
): Promise<{ blindedHex: string; r: bigint }> {
  const n = hexToBigInt(pub.n_hex);
  const e = BigInt(pub.e_dec);
  const m = await sha256ToBigInt(token);       // <-- match backend

  if (m >= n) throw new Error("message too large for modulus");
  const r = randomCoprimeBelow(n);
  const blinded = (modPow(r, e, n) * m) % n;
  return { blindedHex: bigIntToHex(blinded), r };
}

// s = s' * r^{-1} mod n
export function unblindSignature(
  signedBlindedHex: string,
  r: bigint,
  pub: RsaPub
): string {
  const n = hexToBigInt(pub.n_hex);
  const sPrime = hexToBigInt(signedBlindedHex);
  const rInv = modInv(r, n);
  const s = (sPrime * rInv) % n;
  return bigIntToHex(s);
}