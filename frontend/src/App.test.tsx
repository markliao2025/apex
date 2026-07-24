import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const fetchUser = vi.hoisted(() => vi.fn().mockResolvedValue(undefined));
const hasStoredSession = vi.hoisted(() => vi.fn());

vi.mock("./stores/authStore", () => ({
  useAuthStore: () => ({
    isAuthenticated: false,
    fetchUser,
  }),
}));

vi.mock("./lib/api", () => ({
  authApi: {
    hasStoredSession,
  },
}));

describe("App routing", () => {
  beforeEach(() => {
    fetchUser.mockClear();
    hasStoredSession.mockReset();
  });

  it("redirects an unauthenticated protected route to login", async () => {
    hasStoredSession.mockReturnValue(false);
    render(
      <MemoryRouter initialEntries={["/demo/replay"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Apex")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /try the synthetic demo/i }),
    ).toBeInTheDocument();
    expect(fetchUser).not.toHaveBeenCalled();
  });

  it("restores the user only when a stored session exists", async () => {
    hasStoredSession.mockReturnValue(true);

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Apex")).toBeInTheDocument();
    expect(fetchUser).toHaveBeenCalledOnce();
  });
});
