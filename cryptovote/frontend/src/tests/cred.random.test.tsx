// frontend/src/lib/__tests__/cred.random.test.ts
import { genToken } from "../lib/cred";

// Ensure Web Crypto exists in Jest (Node) env
if (!(globalThis as any).crypto?.getRandomValues) {
  const { webcrypto } = require("crypto");
  Object.defineProperty(globalThis, "crypto", {
    value: webcrypto,
    configurable: true,
  });
}

const BASE64URL = /^[A-Za-z0-9_-]+$/;

describe("genToken() CSPRNG properties", () => {
  it("emits base64url tokens (URL-safe, no padding)", () => {
    const t = genToken();
    expect(typeof t).toBe("string");
    expect(t).toMatch(BASE64URL);
    expect(t.includes("=")).toBe(false);
  });

  it("calls crypto.getRandomValues under the hood (at least once)", () => {
    const orig = global.crypto.getRandomValues;
    const spy = jest.fn((buf: Uint8Array) => orig.call(global.crypto, buf));
    (global.crypto as any).getRandomValues = spy;

    genToken();

    expect(spy).toHaveBeenCalled();
    (global.crypto as any).getRandomValues = orig; // restore
  });

  it("shows no collisions across many draws and roughly uniform length", () => {
    const N = 5000; // bump to 10000 in CI if you like
    const set = new Set<string>();
    const lens: number[] = [];

    for (let i = 0; i < N; i++) {
      const t = genToken();
      set.add(t);
      lens.push(t.length);
      expect(t).toMatch(BASE64URL);
      expect(t.includes("=")).toBe(false);
    }

    // ✅ collision-free in sample
    expect(set.size).toBe(N);

    // ✅ length is stable (or nearly)
    const minL = Math.min(...lens);
    const maxL = Math.max(...lens);
    expect(maxL - minL).toBeLessThanOrEqual(1);
  });
});
