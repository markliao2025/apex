import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

const fetchUser = vi.hoisted(() => vi.fn().mockResolvedValue(undefined));

vi.mock("./stores/authStore", () => ({
  useAuthStore: () => ({
    isAuthenticated: false,
    fetchUser,
  }),
}));

describe("App routing", () => {
  it("redirects an unauthenticated protected route to login", async () => {
    render(
      <MemoryRouter initialEntries={["/demo/replay"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Apex")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /try the synthetic demo/i }),
    ).toBeInTheDocument();
    expect(fetchUser).toHaveBeenCalled();
  });
});
