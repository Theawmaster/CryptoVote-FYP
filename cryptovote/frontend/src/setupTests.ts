// src/setupTests.ts
// Polyfill Web Crypto for Jest (Node/JSDOM)

// 1) Extend expect with jest-dom matchers
import "@testing-library/jest-dom";

// 2) Web Crypto polyfill for JSDOM (you already have this; keep it)
try {
  // Node 16+ exposes a WHATWG Crypto via crypto.webcrypto
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { webcrypto } = require("crypto");
  if (webcrypto && !globalThis.crypto) {
    Object.defineProperty(globalThis, "crypto", {
      value: webcrypto,
      configurable: true,
      writable: false,
      enumerable: true,
    });
  }
} catch {
  // Fallback: implement just getRandomValues via randomBytes
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { randomBytes } = require("crypto");
  if (!globalThis.crypto) {
    (globalThis as any).crypto = {
      getRandomValues: (arr: Uint8Array) => {
        const buf = randomBytes(arr.length);
        arr.set(buf);
        return arr;
      },
    };
  }
}
