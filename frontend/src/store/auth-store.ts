import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "../services/api/types";

export interface AuthState {
  token: string | null;
  user: User | null;
  tempToken: string | null;
  setupToken: string | null;
  qrUri: string | null;
  setSession: (token: string, user: User) => void;
  setTempToken: (tempToken: string | null) => void;
  setSetupToken: (payload: { setupToken: string; qrUri: string | null }) => void;
  setUser: (user: User | null) => void;
  clearSession: () => void;
}

export const authStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      tempToken: null,
      setupToken: null,
      qrUri: null,
      setSession: (token, user) =>
        set({
          token,
          user,
          tempToken: null,
          setupToken: null,
          qrUri: null,
        }),
      setTempToken: (tempToken) =>
        set({
          tempToken,
        }),
      setSetupToken: ({ setupToken, qrUri }) =>
        set({
          setupToken,
          qrUri,
        }),
      setUser: (user) => set({ user }),
      clearSession: () =>
        set({
          token: null,
          user: null,
          tempToken: null,
          setupToken: null,
          qrUri: null,
        }),
    }),
    {
      name: "tg-auth-storage",
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);

export const useAuthStore = <T>(selector: (state: AuthState) => T) =>
  authStore(selector);

