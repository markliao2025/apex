import { create } from "zustand";
import { User } from "../types";
import { authApi } from "../lib/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  startDemo: () => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await authApi.login(email, password);
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Login failed";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  register: async (email: string, password: string, name?) => {
    set({ isLoading: true, error: null });
    try {
      await authApi.register(email, password, name);
      // Auto-login after registration
      const data = await authApi.login(email, password);
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Registration failed";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  startDemo: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await authApi.demoSession();
      set({ user: data.user, isAuthenticated: true, isLoading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Demo is unavailable";
      set({ isLoading: false, error: message });
      throw err;
    }
  },

  logout: () => {
    authApi.logout();
    set({ user: null, isAuthenticated: false, error: null });
  },

  fetchUser: async () => {
    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true });
    } catch {
      authApi.logout();
      set({ user: null, isAuthenticated: false });
    }
  },

  clearError: () => set({ error: null }),
}));
