// src/ctx/CredentialContext.tsx
import React, { createContext, useContext, useMemo, useState } from "react";

export type Cred = {
  tracker: any;
  electionId: string;
  token: string;
  signatureHex: string;
  rsaKeyId: string;
};

type Ctx = {
  cred: Cred | null;
  setCred: (c: Cred | null) => void;
  clear: () => void;
};

const CredentialCtx = createContext<Ctx | undefined>(undefined);

export const CredentialProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cred, setCredState] = useState<Cred | null>(null);

  const setCred = (c: Cred | null) => setCredState(c);
  const clear = () => setCredState(null);

  // IMPORTANT: depend on `cred` so consumers re-render when it changes.
  // If this was useMemo(..., []), the value would never update -> your symptom.
  const value = useMemo(() => ({ cred, setCred, clear }), [cred]);

  return <CredentialCtx.Provider value={value}>{children}</CredentialCtx.Provider>;
};

export function useCredential(): Ctx {
  const v = useContext(CredentialCtx);
  if (!v) throw new Error("useCredential must be used within <CredentialProvider>");
  return v;
}
