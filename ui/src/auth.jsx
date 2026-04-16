import React, { createContext, useCallback, useContext, useMemo, useState } from "react";

const Ctx = createContext(null);

const STORAGE_KEY = "ajaia_session";

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { token: null, user: null };
    const p = JSON.parse(raw);
    if (!p.token || !p.user) return { token: null, user: null };
    return p;
  } catch {
    return { token: null, user: null };
  }
}

export function AuthProvider({ children }) {
  const [state, setState] = useState(() =>
    typeof window === "undefined" ? { token: null, user: null } : load(),
  );

  const setSession = useCallback((token, user) => {
    const next = { token, user };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setState(next);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setState({ token: null, user: null });
  }, []);

  const v = useMemo(
    () => ({ ...state, setSession, logout }),
    [state, setSession, logout],
  );

  return <Ctx.Provider value={v}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const x = useContext(Ctx);
  if (!x) throw new Error("useAuth outside provider");
  return x;
}
