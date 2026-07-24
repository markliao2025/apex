import { beforeEach, describe, expect, it, vi } from "vitest";

import { authApi } from "../lib/api";
import { useAuthStore } from "./authStore";

vi.mock("../lib/api", () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getMe: vi.fn(),
  },
}));

const demoUser = {
  id: "00000000-0000-0000-0000-000000000001",
  email: "demo@apex.local",
  name: "Demo Operator",
  plan: "demo",
  created_at: "2026-07-04T06:30:00Z",
};

describe("auth store", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  it("registers and performs exactly one login", async () => {
    vi.mocked(authApi.register).mockResolvedValue(demoUser);
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: "access",
      refresh_token: "refresh",
      user: demoUser,
    });

    await useAuthStore.getState().register(
      "demo@apex.local",
      "demo-password",
      "Demo Operator",
    );

    expect(authApi.register).toHaveBeenCalledOnce();
    expect(authApi.login).toHaveBeenCalledOnce();
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it("clears local authentication when fetching the user fails", async () => {
    vi.mocked(authApi.getMe).mockRejectedValue(new Error("unauthorized"));

    await useAuthStore.getState().fetchUser();

    expect(authApi.logout).toHaveBeenCalledOnce();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
