/** Shimmer placeholder while TipTap content loads (matches editor chrome). */
export function EditorSkeleton() {
  const pills = [28, 28, 28, 38, 38, 32, 32];
  return (
    <div
      className="editor-with-toolbar notes-editor-skeleton"
      aria-busy="true"
      aria-label="Loading editor"
    >
      <div className="editor-toolbar notes-skel-toolbar">
        {pills.map((w, i) => (
          <span
            key={i}
            className="notes-skel-pill notes-skel-shimmer"
            style={{ width: `${w}px` }}
          />
        ))}
      </div>
      <div className="notes-skel-body">
        <div className="notes-skel-line notes-skel-line-title notes-skel-shimmer" />
        <div className="notes-skel-line notes-skel-shimmer" />
        <div className="notes-skel-line notes-skel-line-wide notes-skel-shimmer" />
        <div className="notes-skel-line notes-skel-shimmer" />
        <div className="notes-skel-line notes-skel-line-narrow notes-skel-shimmer" />
      </div>
    </div>
  );
}

/** Full document layout while metadata is loading. */
export function DocumentPageSkeleton() {
  return (
    <div className="notes-doc-page" aria-busy="true" aria-label="Loading document">
      <div className="notes-doc-scroll">
        <div className="notes-doc-inner">
          <div className="notes-skel-title-share">
            <div className="notes-skel-title-block notes-skel-shimmer" />
            <div className="notes-skel-share-ghost notes-skel-shimmer" />
          </div>
          <div className="notes-skel-file-toolbar">
            <div className="notes-skel-chip notes-skel-shimmer" />
            <div className="notes-skel-chip notes-skel-shimmer" />
            <div className="notes-skel-hint notes-skel-shimmer" />
          </div>
          <div className="notes-editor-surface">
            <EditorSkeleton />
          </div>
          <div className="notes-skel-att-bar notes-skel-shimmer" />
        </div>
      </div>
    </div>
  );
}

/** Public link page shell. */
export function LinkPageSkeleton() {
  return (
    <div className="link-public-shell" aria-busy="true" aria-label="Loading shared document">
      <header className="link-public-top">
        <div className="notes-skel-chip notes-skel-shimmer" style={{ width: "4rem", height: "1.25rem" }} />
        <div className="notes-skel-chip notes-skel-shimmer" style={{ width: "6rem", height: "1.25rem" }} />
      </header>
      <div className="link-public-main">
        <div className="notes-skel-line-title notes-skel-shimmer link-public-title-skel" />
        <div className="notes-editor-surface">
          <EditorSkeleton />
        </div>
      </div>
    </div>
  );
}
