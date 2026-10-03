import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { me } from "@/api/auth";
import { AUTH_EXPIRED_EVENT, getAccessToken } from "@/api/client";
import type { AuthUser } from "@/types/content";

interface AdminAuthState {
  status: "loading" | "authed" | "unauthed";
  user: AuthUser | null;
  refresh: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthState | null>(null);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AdminAuthState["status"]>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);

  async function check() {
    if (!getAccessToken()) {
      setStatus("unauthed");
      setUser(null);
      return;
    }
    try {
      const u = await me();
      if (u.role === "admin") {
        setUser(u);
        setStatus("authed");
      } else {
        setUser(null);
        setStatus("unauthed");
      }
    } catch {
      setUser(null);
      setStatus("unauthed");
    }
  }

  useEffect(() => {
    check();
  }, []);

  // Fired by the API client when a refresh fails for good (token expired or revoked).
  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      setStatus("unauthed");
    };
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  return (
    <AdminAuthContext.Provider value={{ status, user, refresh: check }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext);
  if (!ctx) throw new Error("useAdminAuth must be used within AdminAuthProvider");
  return ctx;
}
