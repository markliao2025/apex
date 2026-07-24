import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import LoginPage from "./LoginPage";

const store = vi.hoisted(() => ({
  login: vi.fn(),
  register: vi.fn(),
  startDemo: vi.fn().mockResolvedValue(undefined),
  isLoading: false,
  error: null,
  clearError: vi.fn(),
}));

vi.mock("../stores/authStore", () => ({
  useAuthStore: () => store,
}));

describe("LoginPage", () => {
  it("offers a no-account synthetic demo with a safety warning", async () => {
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/demo/replay" element={<div>Replay route</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText(/synthetic and not for operational decisions/i),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /try the synthetic demo/i }),
    );
    await waitFor(() => expect(store.startDemo).toHaveBeenCalledOnce());
    expect(await screen.findByText("Replay route")).toBeInTheDocument();
  });
});
