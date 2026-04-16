import { useEffect, useState } from "react";
import { useOutletContext, useParams } from "react-router-dom";
import {
  createShareLink,
  downloadAttachment,
  getDocument,
  importTextIntoDocument,
  listAttachments,
  listUsers,
  renameDocument,
  revokeShareLink,
  shareDocument,
  uploadAttachment,
} from "../api.js";
import { useAuth } from "../auth.jsx";
import { DocEditor } from "../components/DocEditor.jsx";
import { DocumentPageSkeleton } from "../components/LoadingSkeleton.jsx";

export function DocWorkspace() {
  const { setDocMeta } = useOutletContext() ?? {};
  const { id } = useParams();
  const { token } = useAuth();
  const [detail, setDetail] = useState(null);
  const [title, setTitle] = useState("");
  const [users, setUsers] = useState([]);
  const [shareEmail, setShareEmail] = useState("");
  const [shareRole, setShareRole] = useState("editor");
  const [linkRole, setLinkRole] = useState("viewer");
  const [linkUrl, setLinkUrl] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [err, setErr] = useState(null);
  const [msg, setMsg] = useState(null);
  const [shareOpen, setShareOpen] = useState(false);
  const [editorEpoch, setEditorEpoch] = useState(0);

  const canEdit = detail?.role === "owner" || detail?.role === "editor";

  useEffect(() => {
    if (!token || !id) return;
    setDetail(null);
    setErr(null);
    let cancelled = false;
    (async () => {
      try {
        const d = await getDocument(token, id);
        if (cancelled) return;
        setDetail(d);
        setTitle(d.title);
        const att = await listAttachments(token, id);
        if (cancelled) return;
        setAttachments(att);
        if (d.role === "owner") {
          const u = await listUsers(token);
          if (!cancelled) setUsers(u);
        }
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, id]);

  useEffect(() => {
    if (!setDocMeta) return;
    if (!detail) {
      setDocMeta(null);
      return;
    }
    setDocMeta({
      title: (title.trim() || detail.title || "Untitled").trim(),
      role: detail.role,
      access: detail.access,
    });
  }, [detail, title, setDocMeta]);

  useEffect(() => {
    return () => setDocMeta?.(null);
  }, [setDocMeta]);

  async function onRename(e) {
    e.preventDefault();
    if (!token || !id || !detail) return;
    setErr(null);
    try {
      const d = await renameDocument(token, id, title.trim() || "Untitled");
      setDetail(d);
      setMsg("Saved");
      window.setTimeout(() => setMsg(null), 1600);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Rename failed");
    }
  }

  async function onShare(e) {
    e.preventDefault();
    if (!token || !id) return;
    setErr(null);
    try {
      await shareDocument(token, id, shareEmail.trim(), shareRole);
      setShareEmail("");
      setMsg(`Shared (${shareRole})`);
      window.setTimeout(() => setMsg(null), 2000);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Share failed");
    }
  }

  async function onCreateLink() {
    if (!token || !id) return;
    setErr(null);
    try {
      const r = await createShareLink(token, id, linkRole);
      const url = `${window.location.origin}/link/${encodeURIComponent(r.token)}`;
      setLinkUrl(url);
      setMsg("Link ready — copy below");
      window.setTimeout(() => setMsg(null), 4000);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Link failed");
    }
  }

  async function onRevokeLink() {
    if (!token || !id) return;
    setErr(null);
    try {
      await revokeShareLink(token, id);
      setLinkUrl(null);
      setMsg("Link revoked");
      window.setTimeout(() => setMsg(null), 2000);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Revoke failed");
    }
  }

  async function refreshAttachments() {
    if (!token || !id) return;
    const att = await listAttachments(token, id);
    setAttachments(att);
  }

  if (!id || !token) return null;
  if (err && !detail) return <div className="notes-page-pad notes-flash notes-flash-error">{err}</div>;
  if (!detail) return <DocumentPageSkeleton />;

  const statusText = err ?? msg;

  return (
    <div className="notes-doc-page">
      <div className="notes-doc-scroll">
        <div className="notes-doc-inner">
          {statusText ? (
            <div className={"notes-status" + (err ? " notes-status-err" : " notes-status-ok")}>{statusText}</div>
          ) : null}

          <div className="notes-title-share-row">
            <form className="notes-title-form-inline" onSubmit={onRename}>
              <input
                type="text"
                className="notes-title-input-minimal"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={detail.role !== "owner"}
                placeholder="Untitled"
                aria-label="Document title"
              />
              {detail.role === "owner" ? (
                <button type="submit" className="notes-btn-text">
                  Save title
                </button>
              ) : null}
            </form>
            {detail.role === "owner" ? (
              <button
                type="button"
                className="notes-btn-text notes-btn-text-strong"
                onClick={() => setShareOpen((v) => !v)}
              >
                {shareOpen ? "Hide sharing" : "Share"}
              </button>
            ) : null}
          </div>

          {shareOpen && detail.role === "owner" ? (
            <section className="notes-share-panel notes-share-panel-compact">
              <form className="notes-share-grid" onSubmit={onShare}>
                <label className="notes-field notes-field-inline">
                  <span className="sr-only">Invite</span>
                  <select
                    value={shareEmail}
                    onChange={(e) => setShareEmail(e.target.value)}
                    className="notes-select"
                  >
                    <option value="">Invite…</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.email}>
                        {u.display_name} ({u.email})
                      </option>
                    ))}
                  </select>
                </label>
                <select
                  value={shareRole}
                  onChange={(e) => setShareRole(e.target.value)}
                  className="notes-select notes-select-narrow"
                  aria-label="Invite permission"
                >
                  <option value="editor">Can edit</option>
                  <option value="viewer">View only</option>
                </select>
                <button type="submit" className="notes-btn notes-btn-primary notes-btn-sm" disabled={!shareEmail}>
                  Invite
                </button>
              </form>
              <div className="notes-link-row notes-link-row-tight">
                <select
                  value={linkRole}
                  onChange={(e) => setLinkRole(e.target.value)}
                  className="notes-select notes-select-narrow"
                  aria-label="Link permission"
                >
                  <option value="viewer">Link: view</option>
                  <option value="editor">Link: edit</option>
                </select>
                <button type="button" className="notes-btn notes-btn-secondary notes-btn-sm" onClick={onCreateLink}>
                  Create link
                </button>
                <button type="button" className="notes-btn notes-btn-ghost notes-btn-sm" onClick={onRevokeLink}>
                  Revoke
                </button>
              </div>
              {linkUrl ? <input readOnly className="notes-link-input notes-link-input-tight" value={linkUrl} /> : null}
            </section>
          ) : null}

          {canEdit ? (
            <div className="notes-file-toolbar" role="group" aria-label="Import and attach">
              <label className="notes-file-toolbar-btn">
                Replace from file
                <input
                  type="file"
                  accept=".txt,.md,.markdown,text/plain"
                  hidden
                  onChange={async (e) => {
                    const f = e.target.files?.[0];
                    e.target.value = "";
                    if (!f || !token) return;
                    setErr(null);
                    setMsg(null);
                    try {
                      await importTextIntoDocument(token, id, f);
                      const d = await getDocument(token, id);
                      setDetail(d);
                      setTitle(d.title);
                      setEditorEpoch((n) => n + 1);
                      setMsg("Draft updated from file");
                      window.setTimeout(() => setMsg(null), 2000);
                    } catch (ex) {
                      setErr(ex instanceof Error ? ex.message : "Import failed");
                    }
                  }}
                />
              </label>
              <label className="notes-file-toolbar-btn">
                Attach
                <input
                  type="file"
                  hidden
                  onChange={async (e) => {
                    const f = e.target.files?.[0];
                    e.target.value = "";
                    if (!f || !token) return;
                    setErr(null);
                    setMsg(null);
                    try {
                      await uploadAttachment(token, id, f);
                      await refreshAttachments();
                      setMsg("Attachment added");
                      window.setTimeout(() => setMsg(null), 2000);
                    } catch (ex) {
                      setErr(ex instanceof Error ? ex.message : "Upload failed");
                    }
                  }}
                />
              </label>
              <span className="notes-file-toolbar-hint" title="Replace: UTF-8 .txt/.md only, not .docx. Attach: any file, max 5 MB.">
                .txt / .md · max 5 MB attach
              </span>
            </div>
          ) : null}

          <div className="notes-editor-surface">
            <DocEditor key={`${id}-${editorEpoch}`} docId={id} authToken={token} detail={detail} />
          </div>

          <details className="notes-att-fold" open={attachments.length > 0}>
            <summary className="notes-att-fold-summary">
              Attachments
              {attachments.length > 0 ? (
                <span className="notes-att-count">{attachments.length}</span>
              ) : null}
            </summary>
            <ul className="notes-att-list notes-att-list-compact">
              {attachments.map((a) => (
                <li key={a.id}>
                  <button
                    type="button"
                    className="notes-att-link"
                    onClick={() =>
                      downloadAttachment(token, id, a.id, a.filename).catch((e) =>
                        setErr(e instanceof Error ? e.message : "Download failed"),
                      )
                    }
                  >
                    {a.filename}
                  </button>
                  <span className="notes-att-size">{a.byte_size} B</span>
                </li>
              ))}
              {attachments.length === 0 ? <li className="notes-att-empty">None yet</li> : null}
            </ul>
          </details>
        </div>
      </div>
    </div>
  );
}
