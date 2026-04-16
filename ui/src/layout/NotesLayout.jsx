import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { createDocument, importText, listDocuments } from "../api.js";
import { useAuth } from "../auth.jsx";
import { FileUsageGuide } from "../components/FileUsageGuide.jsx";

const SIDEBAR_KEY = "ajaia-notes-sidebar";

/** Must match backend `_TEXT_IMPORT` in documents router. */
const TEXT_IMPORT_EXT = new Set([".txt", ".md", ".markdown"]);

function firstImportableFile(fileList) {
  if (!fileList?.length) return null;
  for (let i = 0; i < fileList.length; i++) {
    const f = fileList[i];
    const lower = f.name.toLowerCase();
    const dot = lower.lastIndexOf(".");
    const ext = dot >= 0 ? lower.slice(dot) : "";
    if (TEXT_IMPORT_EXT.has(ext)) return f;
  }
  return null;
}

function IconPanelLeft({ open }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      {open ? (
        <>
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M9 3v18" />
        </>
      ) : (
        <>
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M9 3v18M15 9l3 3-3 3" />
        </>
      )}
    </svg>
  );
}

function IconPlus() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function NotesLayout() {
  const { token, user, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const [docs, setDocs] = useState([]);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showSidebar, setShowSidebar] = useState(() => {
    try {
      const v = localStorage.getItem(SIDEBAR_KEY);
      return v !== "0";
    } catch {
      return true;
    }
  });
  const [newNameOpen, setNewNameOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [docMeta, setDocMeta] = useState(null);
  const [dropHover, setDropHover] = useState(false);
  const dragDepth = useRef(0);

  const outletCtx = useMemo(() => ({ setDocMeta }), []);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const d = await listDocuments(token);
      setDocs(d);
      setErr(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed to load documents");
    }
  }, [token]);

  useEffect(() => {
    refresh();
  }, [refresh, loc.pathname]);

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, showSidebar ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [showSidebar]);

  async function onCreateNamed() {
    if (!token || !newName.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      const doc = await createDocument(token, newName.trim());
      setNewName("");
      setNewNameOpen(false);
      await refresh();
      nav(`/doc/${doc.id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function onImport(f) {
    if (!token || !f) return;
    setBusy(true);
    setErr(null);
    try {
      const doc = await importText(token, f);
      await refresh();
      nav(`/doc/${doc.id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Import failed");
    } finally {
      setBusy(false);
    }
  }

  function onMainDragEnter(e) {
    if (!token || busy) return;
    if (![...e.dataTransfer.types].includes("Files")) return;
    e.preventDefault();
    dragDepth.current += 1;
    setDropHover(true);
  }

  function onMainDragLeave() {
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setDropHover(false);
  }

  function onMainDragOver(e) {
    if (!token || busy) return;
    if (![...e.dataTransfer.types].includes("Files")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  }

  function onMainDrop(e) {
    dragDepth.current = 0;
    setDropHover(false);
    if (!token || busy) return;
    e.preventDefault();
    const f = firstImportableFile(e.dataTransfer.files);
    if (f) void onImport(f);
    else
      setErr("Drop a .txt, .md, or .markdown file (UTF-8).");
  }

  const readOnlyBadge =
    docMeta?.role === "viewer" ? (
      <span className="notes-pill notes-pill-muted">View only</span>
    ) : null;

  return (
    <div className="notes-app">
      <header className="notes-topbar">
        <div className="notes-topbar-left">
          <button
            type="button"
            className="notes-icon-btn"
            title={showSidebar ? "Hide sidebar" : "Show sidebar"}
            onClick={() => setShowSidebar((v) => !v)}
          >
            <IconPanelLeft open={showSidebar} />
          </button>
          <span className="notes-topbar-divider" aria-hidden />
          <div className="notes-app-badge" aria-hidden>
            A
          </div>
          <span className="notes-topbar-brand">Docs</span>
          <span className="notes-topbar-divider" aria-hidden />
        </div>
        <div className="notes-topbar-center">
          {docMeta ? (
            <div className="notes-topbar-doc-block">
              <div className="notes-topbar-doc-line">
                <span className="notes-topbar-doc-title">{docMeta.title || "Untitled"}</span>
                {readOnlyBadge}
              </div>
              <span className="notes-topbar-doc-sub">
                {docMeta.access === "owner"
                  ? "Owned"
                  : docMeta.access === "link"
                    ? "Link"
                    : "Shared"}
                {" · "}
                {docMeta.role === "owner"
                  ? "Owner"
                  : docMeta.role === "editor"
                    ? "Editor"
                    : "Viewer"}
              </span>
            </div>
          ) : (
            <span className="notes-topbar-placeholder">Your workspace</span>
          )}
        </div>
        <div className="notes-topbar-right">
          <span className="notes-user-name">{user?.display_name}</span>
          <button type="button" className="notes-btn notes-btn-ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      {err ? <div className="notes-flash notes-flash-error">{err}</div> : null}

      <div className="notes-body">
        {showSidebar ? (
          <aside className="notes-sidebar">
            <div className="notes-sidebar-head">
              <div className="notes-sidebar-head-row">
                <h2 className="notes-sidebar-title">Documents</h2>
                <button
                  type="button"
                  className="notes-icon-btn"
                  title="New document"
                  disabled={busy}
                  onClick={() => setNewNameOpen(true)}
                >
                  <IconPlus />
                </button>
              </div>
              {newNameOpen ? (
                <input
                  className="notes-sidebar-input"
                  autoFocus
                  placeholder="Title…"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void onCreateNamed();
                    if (e.key === "Escape") {
                      setNewNameOpen(false);
                      setNewName("");
                    }
                  }}
                  onBlur={() => {
                    setNewNameOpen(false);
                    setNewName("");
                  }}
                />
              ) : null}
            </div>
            <div className="notes-sidebar-list">
              {docs.length === 0 ? (
                <div className="notes-sidebar-empty">
                  <p>No documents yet</p>
                  <p className="notes-sidebar-empty-hint">Use +, New doc from file, or drop .txt / .md here</p>
                </div>
              ) : (
                docs.map((d) => (
                  <NavLink
                    key={d.id}
                    to={`/doc/${d.id}`}
                    className={({ isActive }) =>
                      "notes-doc-row" + (isActive ? " notes-doc-row-active" : "")
                    }
                  >
                    <div className="notes-doc-row-body">
                      <div className="notes-doc-row-title">{d.title}</div>
                      <div className="notes-doc-row-meta">
                        {d.access === "owner"
                          ? "Owned"
                          : d.share_role === "viewer"
                            ? "Shared · view"
                            : "Shared · edit"}
                      </div>
                    </div>
                    <time className="notes-doc-row-time" dateTime={d.updated_at}>
                      {new Date(d.updated_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                      })}
                    </time>
                  </NavLink>
                ))
              )}
            </div>
            <div className="notes-sidebar-foot">
              <label className="notes-btn notes-btn-secondary notes-import-label notes-import-compact">
                New from .txt / .md
                <input
                  type="file"
                  accept=".txt,.md,.markdown,text/plain"
                  hidden
                  disabled={busy}
                  onChange={(e) => {
                    const f = e.target.files?.[0] ?? null;
                    e.target.value = "";
                    void onImport(f);
                  }}
                />
              </label>
              <FileUsageGuide />
            </div>
          </aside>
        ) : null}

        <main
          className={"notes-main" + (dropHover ? " notes-main-drop-target" : "")}
          onDragEnter={onMainDragEnter}
          onDragLeave={onMainDragLeave}
          onDragOver={onMainDragOver}
          onDrop={onMainDrop}
        >
          {dropHover ? (
            <div className="notes-drop-hint" aria-hidden>
              <span>Drop to import .txt or .md</span>
            </div>
          ) : null}
          <Outlet context={outletCtx} />
        </main>
      </div>
    </div>
  );
}
