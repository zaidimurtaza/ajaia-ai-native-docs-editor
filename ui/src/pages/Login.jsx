import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api.js";
import { useAuth } from "../auth.jsx";

export function Login() {
  const { setSession } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("alice@example.com");
  const [password, setPassword] = useState("demo");
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const r = await login(email.trim(), password);
      setSession(r.access_token, r.user);
      nav("/", { replace: true });
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="layout-center">
      <div className="card login-card">
        <div className="brand">
          <span className="logo">Ajaia</span>
          <h1>Docs</h1>
          <p className="muted">Mock auth — try Alice or Bob (password: demo)</p>
        </div>
        <form onSubmit={onSubmit} className="stack">
          <label className="field">
            <span>Email</span>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {err ? <div className="error-banner">{err}</div> : null}
          <button type="submit" className="btn primary" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
