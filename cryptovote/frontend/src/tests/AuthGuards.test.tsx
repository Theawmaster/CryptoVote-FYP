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

// frontend/src/pages/voter/__tests__/AuthGuards.test.tsx
import React from "react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { render, screen, waitFor } from "@testing-library/react";
import { useEnsureVoter } from "../hooks/useAuthGuard";

const Protected: React.FC = () => {
  useEnsureVoter();
  return <div>Protected Voter Page</div>;
};

function jsonRes(status: number, body?: any) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body ?? {},
    headers: new Headers({ "content-type": "application/json" }),
  } as unknown as Response;
}

describe("useEnsureVoter()", () => {
  afterEach(() => {
    (global.fetch as any) = undefined;
    jest.clearAllMocks();
  });

  it("redirects to /auth when /whoami is invalid", async () => {
    (global as any).fetch = jest.fn(async (url: string) => {
      if (url === "/whoami") return jsonRes(401, { error: "unauthenticated" });
      return jsonRes(200, {});
    });

    render(
      <MemoryRouter initialEntries={["/voter/protected"]}>
        <Routes>
          <Route path="/voter/protected" element={<Protected />} />
          <Route path="/auth" element={<div>Auth Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("Auth Page")).toBeInTheDocument());
  });

  it("stays when /whoami is a valid voter", async () => {
    (global as any).fetch = jest.fn(async (url: string) => {
      if (url === "/whoami") return jsonRes(200, { role: "voter", is_verified: true, logged_in: true });
      return jsonRes(200, {});
    });

    render(
      <MemoryRouter initialEntries={["/voter/protected"]}>
        <Routes>
          <Route path="/voter/protected" element={<Protected />} />
          <Route path="/auth" element={<div>Auth Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("Protected Voter Page")).toBeInTheDocument());
  });
});
