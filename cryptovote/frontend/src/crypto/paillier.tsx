// src/crypto/paillier.ts
function modPow(base: bigint, exp: bigint, mod: bigint): bigint {
  let result = 1n % mod, b = ((base % mod) + mod) % mod, e = exp;
  while (e > 0n) { if (e & 1n) result = (result * b) % mod; b = (b * b) % mod; e >>= 1n; }
  return result;
}
function gcd(a: bigint, b: bigint): bigint {
  let x = a < 0n ? -a : a, y = b < 0n ? -b : b;
  while (y) { const t = y; y = x % y; x = t; }
  return x;
}
function randomCoprimeBelow(n: bigint): bigint {
  const bits = n.toString(2).length;
  const len = Math.ceil(bits / 8) + 8;
  const buf = new Uint8Array(len);
  for (;;) {
    crypto.getRandomValues(buf);
    let r = 0n; for (let i = 0; i < buf.length; i++) r = (r << 8n) + BigInt(buf[i]);
    r %= n;
    if (r > 0n && gcd(r, n) === 1n) return r;
  }
}

/** Encrypt m ∈ {0,1} with Paillier. g defaults to n+1. Return base-10 string. */
export function paillierEncryptBitToDecString(bit: 0|1, nDec: string, gDec?: string): string {
  const n = BigInt(nDec), g = gDec ? BigInt(gDec) : (n + 1n);
  const n2 = n * n;
  const r = randomCoprimeBelow(n);
  const m = BigInt(bit);
  const c = (modPow(g, m, n2) * modPow(r, n, n2)) % n2;
  return c.toString();
}
