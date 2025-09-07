// ✅ Lightweight virtual mock for react-router-dom so we don't need the real package
jest.mock("react-router-dom", () => {
  const React = require("react");
  return {
    MemoryRouter: ({ children }: any) => <div>{children}</div>,
    Routes: ({ children }: any) => <>{children}</>,
    Route: ({ element }: any) => element,
    useParams: () => ({ id: "election_X" }),
    useNavigate: () => jest.fn(),
    useLocation: () => ({ state: null }),
    Link: ({ children }: any) => <>{children}</>,
  };
}, { virtual: true });

// frontend/src/tests/VoterBallotPage.e2ee.test.tsx
import React from "react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import VoterBallotPage from "../pages/voter/VoterBallotPage";


// --- Mocks for hooks/contexts we don’t want to exercise here
jest.mock("../hooks/useAuthGuard", () => ({ useEnsureVoter: () => {} }));
jest.mock("../hooks/useBackForwardLock", () => ({ useBackForwardLock: () => {} }));
jest.mock("../ctx/CredentialContext", () => ({
  useCredential: () => ({
    cred: { electionId: "election_X", token: "tkn", signatureHex: "sig", rsaKeyId: "rsa-demo" },
    setCred: () => {},
    clear: () => {},
  }),
}));

// --- Force E2EE on
jest.mock("../config/flags", () => ({ E2EE_ENABLED: 1 }));

// --- Mock paillier services & crypto
const nHex = "c1e3a9b5f7d2"; // arbitrary hex for a big n
jest.mock("../services/paillier", () => ({
  fetchPaillierKey: async () => ({ key_id: "paillier-K", nHex }),
}));

jest.mock("../crypto/paillier", () => ({
  paillierEncryptBitToDecString: (bit: any, nDec: string | number | bigint | boolean) => {
    const big = BigInt(nDec);
    const n2 = big * big;
    // return a plausible ciphertext < n^2
    return (n2 - BigInt(42)).toString(10);
  },
}));

function jsonOk(body: any) {
  return {
    ok: true,
    json: async () => body,
    headers: new Headers({ "content-type": "application/json" }),
  } as unknown as Response;
}

describe("VoterBallotPage E2EE submit", () => {
  beforeEach(() => {
    (global as any).fetch = jest.fn(async (url: string) => {
      if (url.startsWith("/voter/elections/")) {
        return jsonOk({
          id: "election_X",
          name: "My Election",
          rsa_key_id: "rsa-demo",
          candidates: [
            { id: "c1", name: "Alice" },
            { id: "c2", name: "Bob" },
            { id: "c3", name: "Chai" },
          ],
        });
      }
      if (url === "/cast-vote") return jsonOk({ message: "ok" });
      return jsonOk({});
    });
  });

  it("sends ballot (and omits candidate_id) when E2EE is enabled", async () => {
    render(
      <MemoryRouter initialEntries={["/voter/elections/election_X"]}>
        <Routes>
          <Route path="/voter/elections/:id" element={<VoterBallotPage />} />
        </Routes>
      </MemoryRouter>
    );

    // wait for candidates
    await screen.findByText("Alice");

    // click “Vote” for Bob
    const voteBtns = screen.getAllByRole("button", { name: /vote for/i });
    fireEvent.click(voteBtns[1]);
    const confirm = await screen.findByRole("button", { name: /confirm & cast/i });
    fireEvent.click(confirm);

    // wait for POST to happen (flushes React state updates too)
    await waitFor(() => {
    expect((global.fetch as jest.Mock)).toHaveBeenCalledWith(
        "/cast-vote",
        expect.any(Object)
    );
    });

    // inspect the POST /cast-vote
    const calls = (global.fetch as jest.Mock).mock.calls;
    const castCall = calls.find(([u]) => u === "/cast-vote");
    expect(castCall).toBeTruthy();

    const body = JSON.parse(castCall![1]!.body as string);

    expect(body.candidate_id).toBeUndefined();
    expect(body.ballot).toBeTruthy();
    expect(body.ballot.scheme).toBe("paillier-1hot");
    expect(typeof body.ballot.key_id).toBe("string");
    expect(body.ballot.entries).toHaveLength(3);

    // rough check that c ~ n^2 (big decimal string)
    const n2Digits = (BigInt("0x" + nHex) ** 2n).toString(10).length;
    for (const ent of body.ballot.entries) {
      expect(typeof ent.candidate_id).toBe("string");
      expect(String(ent.c)).toMatch(/^\d+$/);
      expect(String(ent.c).length).toBeGreaterThanOrEqual(n2Digits - 1);
    }
  });
});
