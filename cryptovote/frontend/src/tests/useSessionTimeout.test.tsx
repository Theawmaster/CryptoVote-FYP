// frontend/src/hooks/__tests__/useSessionTimeout.test.tsx
import React from "react";
import { render, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useSessionTimeout } from "../hooks/useSessionTimeout";

// Small harness to mount the hook and expose actions for the test
const HookHarness: React.FC = () => {
  const api = useSessionTimeout();
  // Expose for imperative calls in tests (logoutNow / staySignedIn)
  (window as any).__sessionHook = api;
  return (
    <div>
      <div data-testid="warn">{String(api.showWarn)}</div>
      <div data-testid="secs">{api.secondsLeft ?? ""}</div>
      <button onClick={api.logoutNow}>logoutNow</button>
      <button onClick={api.staySignedIn}>staySignedIn</button>
    </div>
  );
};

// helper to build a Response-like object
function jsonRes(status: number, body?: any): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body ?? {},
    headers: new Headers({ "content-type": "application/json" }),
  } as unknown as Response;
}

describe("useSessionTimeout (polling/redirect behavior)", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    // Fake timers so we can advance countdowns
    jest.useFakeTimers();

    // Make window.location.replace testable
    // (redefine location with a spyable replace)
    delete (window as any).location;
    // minimal stub with replace spy + pathname
    (window as any).location = {
      ...originalLocation,
      pathname: "/",
      replace: jest.fn(),
    };

    // Fresh fetch mock each test
    (global as any).fetch = jest.fn();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();

    // restore location
    delete (window as any).location;
    (window as any).location = originalLocation;

    jest.clearAllMocks();
  });

  it("redirects to /auth when the server reports session invalid (idle → 401)", async () => {
    // 1st status: logged in, about to expire (idle_remaining=1)
    // 2nd status (after countdown): 401 → hook should redirect
    (global.fetch as jest.Mock).mockImplementation(async (url: string) => {
      if (url === "/session/status") {
        // First call returns nearly-expired session
        if (!(global as any).__firstStatusSent) {
          (global as any).__firstStatusSent = true;
          return jsonRes(200, {
            logged_in: true,
            idle_remaining: 1,
            absolute_remaining: 1,
            warn_after_secs: 60,
          });
        }
        // Second call: server says unauthenticated
        return jsonRes(401, { error: "unauthenticated" });
      }
      return jsonRes(200, {});
    });

    render(<HookHarness />);

    // Initial poll happens immediately; we should soon enter warn mode
    await waitFor(() =>
      expect((global.fetch as jest.Mock)).toHaveBeenCalledWith(
        "/session/status",
        expect.any(Object)
      )
    );

    // Advance timers 1s so secondsLeft hits 0.
    // The hook's effect will re-check status (which we return as 401).
    jest.advanceTimersByTime(1000);

    await waitFor(() =>
      expect((window.location as any).replace).toHaveBeenCalledWith("/auth")
    );
  });

  it("calls /logout/ and redirects when logoutNow() is invoked", async () => {
    (global.fetch as jest.Mock).mockImplementation(async (url: string) => {
      if (url === "/session/status") {
        // Keep session valid so we don't auto-redirect; we want to test logoutNow
        return jsonRes(200, {
          logged_in: true,
          idle_remaining: 120,
          absolute_remaining: 300,
          warn_after_secs: 60,
        });
      }
      if (url === "/logout/") {
        return jsonRes(200, { ok: true });
      }
      return jsonRes(200, {});
    });

    const { getByText } = render(<HookHarness />);

    // ensure we did an initial status poll
    await waitFor(() =>
      expect((global.fetch as jest.Mock)).toHaveBeenCalledWith(
        "/session/status",
        expect.any(Object)
      )
    );

    // trigger logoutNow via the exposed button
    fireEvent.click(getByText("logoutNow"));

    await waitFor(() =>
      expect((global.fetch as jest.Mock)).toHaveBeenCalledWith(
        "/logout/",
        expect.objectContaining({ method: "POST" })
      )
    );
    await waitFor(() =>
      expect((window.location as any).replace).toHaveBeenCalledWith("/auth")
    );
  });
});
