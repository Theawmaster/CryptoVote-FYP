// src/source/paillier.ts
export type PaillierKeyResp = {
  key_id: string;
  nHex: string;  // hex without 0x
  bits: number;
};
export async function fetchPaillierKey(): Promise<PaillierKeyResp> {
  const r = await fetch("/public-keys/paillier", { credentials: "include", cache: "no-store" });
  if (!r.ok) throw new Error("Failed to fetch Paillier public key");
  return r.json();
}
