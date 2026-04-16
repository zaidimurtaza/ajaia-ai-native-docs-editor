/**
 * Explains file flows (collapsed by default to reduce noise).
 */
export function FileUsageGuide() {
  return (
    <details className="notes-file-guide">
      <summary className="notes-file-guide-summary">File types</summary>
      <div className="notes-file-guide-body">
        <p className="notes-file-guide-lead">
          <strong>New doc:</strong> UTF-8 <code>.txt</code> <code>.md</code> <code>.markdown</code> (sidebar or
          drag-drop). <strong>No .docx.</strong>
        </p>
        <p className="notes-file-guide-lead">
          <strong>Attachment:</strong> any type, max <strong>5 MB</strong> — stored for download, not editor text.
        </p>
        <p className="notes-file-guide-lead">
          <strong>Into draft:</strong> same text types on the doc page — replaces body; title unchanged.
        </p>
      </div>
    </details>
  );
}
