import { postJSON } from "./http";
import { paillierEncryptBitToDecString } from "../../crypto/paillier";

export type Candidate = { id: string; name: string };
export type ElectionDetail = {
  id: string; name: string; rsa_key_id?: string;
  candidates: Candidate[];
};

export type BallotEntry = { candidate_id: string; c: string };

export type OneHotBallot = {
  scheme: "paillier-1hot";
  exponent: 0;
  key_id: string;
  entries: BallotEntry[];
};

export function buildOneHotBallot(
  detail: ElectionDetail,
  selectedId: string,
  nDec: string,           // Paillier n in decimal (string to avoid BigInt spill)
  keyId: string
): OneHotBallot {
  const entries = detail.candidates.map((c) => {
    const bit: 0 | 1 = c.id === selectedId ? 1 : 0;
    const ciph = paillierEncryptBitToDecString(bit, nDec);
    return { candidate_id: c.id, c: ciph };
  });
  return { scheme: "paillier-1hot", exponent: 0, key_id: keyId, entries };
}

// --- submitters -------------------------------------------------------------

type LegacyCastBody = {
  election_id: string;
  candidate_id: string;
  token: string;
  signature: string;
  tracker: string;
};

type E2EECastBody = {
  election_id: string;
  token: string;
  signature: string;
  ballot: OneHotBallot;
  tracker: string;
};

export async function submitLegacy(body: LegacyCastBody) {
  return postJSON<{ message: string }>("/cast-vote", body);
}

export async function submitE2EE(body: E2EECastBody) {
  return postJSON<{ message: string }>("/cast-vote", body);
}
