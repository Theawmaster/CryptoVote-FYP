import React from "react";
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useBackForwardLock } from "../hooks/useBackForwardLock";

// --- Mock the credential context (must not reference out-of-scope vars)
let mockClearSpy: jest.Mock; // NOTE: starts with "mock" so Jest allows it
jest.mock("../ctx/CredentialContext", () => {
  mockClearSpy = jest.fn();
  return {
    __esModule: true,
    useCredential: () => ({
      cred: { electionId: "EL-LOCK", token: "tkn", ephemeral: true },
      setCred: jest.fn(),
      clear: mockClearSpy,
    }),
  };
});

const Harness: React.FC = () => {
  // Consumer decides what to do on attempted back nav
  const { useCredential } = require("../ctx/CredentialContext");
  const onAttempt = () => {
    if (window.confirm("Leave this page?")) {
      useCredential().clear(); // clear ephemeral creds when user chooses "Leave"
    }
  };

  useBackForwardLock({
    enabled: true,
    onAttempt,
    beforeUnloadMessage: "Unsaved progress will be lost.",
  });

  return <div data-testid="mounted">mounted</div>;
};

describe("useBackForwardLock()", () => {
  let confirmSpy: jest.SpyInstance;

  beforeEach(() => {
    // jsdom may not implement history.forward; ensure it exists & spy it
    if (!("forward" in window.history)) {
      (window.history as any).forward = () => {};
    }
    jest.spyOn(window.history, "forward").mockImplementation(() => {});
    confirmSpy = jest.spyOn(window, "confirm");
    render(<Harness />);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    mockClearSpy.mockReset();
  });

  test("shows a beforeunload prompt when configured", () => {
    const ev = new Event("beforeunload", { cancelable: true }) as any;
    Object.defineProperty(ev, "returnValue", { writable: true, value: "" });
    window.dispatchEvent(ev);

    // Browsers show a prompt if returnValue is set or the event was prevented
    expect(!!ev.returnValue || ev.defaultPrevented).toBe(true);
  });

  test("Back triggers onAttempt; choosing 'Leave' clears ephemeral cred", () => {
    confirmSpy.mockReturnValue(true); // user chooses Leave
    window.dispatchEvent(new PopStateEvent("popstate"));

    expect(confirmSpy).toHaveBeenCalled();
    expect(window.history.forward).toHaveBeenCalled(); // hook cancels the back nav
    expect(mockClearSpy).toHaveBeenCalled();           // consumer cleared creds
  });

  test("Back triggers onAttempt; choosing 'Stay' keeps creds", () => {
    confirmSpy.mockReturnValue(false); // user chooses Stay
    window.dispatchEvent(new PopStateEvent("popstate"));

    expect(confirmSpy).toHaveBeenCalled();
    expect(window.history.forward).toHaveBeenCalled();
    expect(mockClearSpy).not.toHaveBeenCalled();
  });
});
