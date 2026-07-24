import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api, authApi, shouldAttemptTokenRefresh } from "./api";

const originalAdapter = api.defaults.adapter;

describe("authentication response handling", () => {
  beforeEach(() => {
    const values = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
      clear: () => values.clear(),
    });
    window.history.replaceState({}, "", "/login");
  });

  afterEach(() => {
    api.defaults.adapter = originalAdapter;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("does not reload the login page when an anonymous auth check returns 401", async () => {
    const adapter = vi.fn(async (config: InternalAxiosRequestConfig) => {
      const response = {
        config,
        data: { detail: "Not authenticated" },
        headers: {},
        status: 401,
        statusText: "Unauthorized",
      } satisfies AxiosResponse;
      throw { config, response };
    });
    api.defaults.adapter = adapter;

    await expect(authApi.getMe()).rejects.toBeDefined();

    expect(adapter).toHaveBeenCalledOnce();
    expect(window.location.pathname).toBe("/login");
  });

  it("only attempts token refresh when a refresh token exists", () => {
    expect(shouldAttemptTokenRefresh(401, false, null)).toBe(false);
    expect(shouldAttemptTokenRefresh(401, false, "refresh-token")).toBe(true);
    expect(shouldAttemptTokenRefresh(401, true, "refresh-token")).toBe(false);
  });
});
