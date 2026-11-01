"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";

/**
 * Auth context — session persistence, login/logout, role helpers.
 * Backed by the backend's token auth (localStorage token + user).
 */

import {
API_BASE_URL,
AuthUser,Role,ReaderProfile,
apiLogout,
clearSession,
getStoredToken,getStoredUser,
storeSession,
} from "@/lib/api";
import React,{ createContext,useCallback,useContext,useState,useEffect } from "react";

type AuthContextType = {
  user: AuthUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<AuthUser>;
  register: (name: string, username: string, password: string, classroomCode: string) => Promise<string>;
  logout: () => Promise<void>;
  setProfile: (profile: ReaderProfile) => void;
  isTeacher: boolean;
  hasRole: (role: Role) => boolean;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const expired = () => { setUser(null); setLoading(false); };
    window.addEventListener("sf-auth-expired", expired);
    return () => window.removeEventListener("sf-auth-expired", expired);
  }, []);

  // Hydrate from localStorage; verify the token is still valid server-side.
  useDeferredEffect(() => {
    const stored = getStoredUser();
    const token = getStoredToken();
    if (!stored || !token) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    let active = true;
    const current = () => active && getStoredToken() === token;
    const cancel = () => { active = false; controller.abort(); };
    window.addEventListener("pagehide", cancel);
    fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => { if (current()) setUser(data.user); })
      .catch((error) => {
        if (!current() || error?.name === "AbortError") return;
        clearSession();
        setUser(null);
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { cancel(); window.removeEventListener("pagehide", cancel); };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await import("@/lib/api").then((m) => m.apiLogin(username, password));
    storeSession(data.token, data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (name: string, username: string, password: string, classroomCode: string) => {
    const data = await import("@/lib/api").then((m) => m.apiRegister(name, username, password, classroomCode));
    return data.message;
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
  }, []);

  const setProfile = useCallback((profile: ReaderProfile) => {
    const token = getStoredToken();
    const stored = getStoredUser();
    if (!token || stored?.id !== profile.user_id) return;
    const updated = { ...stored, profile, profile_completed: profile.profile_completed, reader_mode: profile.reader_mode };
    storeSession(token, updated);
    setUser(current => current?.id === profile.user_id ? updated : current);
  }, []);

  const hasRole = useCallback((role: Role) => user?.role === role, [user]);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, setProfile, isTeacher: user?.role === "teacher", hasRole }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
