import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { downloadAttachment, getDocumentByLink, listAttachments } from "../api.js";
import { DocEditor } from "../components/DocEditor.jsx";
import { LinkPageSkeleton } from "../components/LoadingSkeleton.jsx";

export function LinkDoc() {
  const { token } = useParams();
  const [detail, setDetail] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const d = await getDocumentByLink(token);
        if (cancelled) return;
        setDetail(d);
        const att = await listAttachments(null, d.id, token);
        if (cancelled) return;
        setAttachments(att);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Failed to load");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (!token) return <NavigateHome />;
  if (err && !detail) return <div className="notes-page-pad notes-flash notes-flash-error">{err}</div>;
  if (!detail) return <LinkPageSkeleton />;

  return (
    <div className="link-public-shell">
      <header className="link-public-top">
        <Link to="/login" className="link-public-signin">
          Sign in
        </Link>
        <div className="notes-badges-row">
          <span className="notes-badge notes-badge-shared">Anyone with link</span>
          <span className="notes-pill">{detail.role === "editor" ? "Can edit" : "View only"}</span>
        </div>
      </header>
      <div className="link-public-main">
        {err ? <div className="notes-status notes-status-err">{err}</div> : null}
        <h1 className="link-public-title">{detail.title}</h1>
        <div className="notes-editor-surface">
          <DocEditor
            key={token}
            docId={detail.id}
            authToken={null}
            linkSlug={token}
            detail={detail}
          />
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
                    downloadAttachment(null, detail.id, a.id, a.filename, token).catch((e) =>
                      setErr(e instanceof Error ? e.message : "Download failed"),
                    )
                  }
                >
                  {a.filename}
                </button>
                <span className="notes-att-size">{a.byte_size} B</span>
              </li>
            ))}
            {attachments.length === 0 ? <li className="notes-att-empty">None</li> : null}
          </ul>
        </details>
      </div>
    </div>
  );
}

function NavigateHome() {
  return (
    <div className="layout-center">
      <p className="muted">
        <Link to="/login" className="link-public-signin">
          Go to sign in
        </Link>
      </p>
    </div>
  );
}
