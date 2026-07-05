import { create } from "zustand";
import { persist } from "zustand/middleware";
import { userRole, type UserRole } from "../lib/schemas";

// Decoded (unverified) view of the access-token payload. The backend is the
// only trust boundary — these claims are used purely to shape the UI (which
// nav links to show), never for authorization decisions.
export interface SessionClaims {
  userId: string;
  orgId: string;
  role: UserRole;
  exp: number;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  claims: SessionClaims | null;
  setTokens: (access: string, refresh: string) => void;
  clear: () => void;
}

function decodeClaims(accessToken: string): SessionClaims | null {
  try {
    const payload = accessToken.split(".")[1];
    if (!payload) return null;
    const json = JSON.parse(
      atob(payload.replace(/-/g, "+").replace(/_/g, "/")),
    ) as Record<string, unknown>;
    const role = userRole.safeParse(json["role"]);
    if (!role.success) return null;
    return {
      userId: String(json["sub"]),
      orgId: String(json["org"]),
      role: role.data,
      exp: Number(json["exp"]),
    };
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      claims: null,
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh, claims: decodeClaims(access) }),
      clear: () => set({ accessToken: null, refreshToken: null, claims: null }),
    }),
    {
      name: "ems-auth",
      // Tokens live in localStorage so a refresh survives reloads. The refresh
      // token rotates on every use (backend reuse-detection revokes the family
      // if a stale one reappears), which bounds the blast radius of XSS theft.
      partialize: (s) => ({ accessToken: s.accessToken, refreshToken: s.refreshToken }),
      onRehydrateStorage: () => (state) => {
        if (state?.accessToken) state.claims = decodeClaims(state.accessToken);
      },
    },
  ),
);

// Non-hook accessors for use inside the ky client (outside React).
export const authSnapshot = () => useAuthStore.getState();
