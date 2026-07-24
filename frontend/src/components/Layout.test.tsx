import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Layout from "./Layout";

const logout = vi.hoisted(() => vi.fn());

vi.mock("../stores/authStore", () => ({
  useAuthStore: () => ({
    user: {
      email: "demo@apex.local",
      name: "Demo Operator",
      plan: "demo",
    },
    logout,
  }),
}));

describe("Layout", () => {
  it("uses a labelled mobile-safe primary navigation", () => {
    render(
      <MemoryRouter initialEntries={["/demo/replay"]}>
        <Layout>
          <p>Demo content</p>
        </Layout>
      </MemoryRouter>,
    );

    const navigation = screen.getByRole("navigation", { name: "Primary" });
    expect(navigation).toHaveClass("grid", "grid-cols-3", "w-full");
    expect(
      screen.getByRole("button", { name: "Log out" }),
    ).toBeInTheDocument();
  });
});
