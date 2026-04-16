/**
 * Context strip for the Ajaia take-home (submission packaging).
 * Replace VIDEO_URL.txt and README deployment URL before submitting.
 */
export function AssignmentBanner() {
  return (
    <aside className="assignment-banner" aria-label="Assignment context">
      <div className="assignment-banner-inner">
        <strong>Ajaia LLC</strong>
        <span className="sep">·</span>
        <span>AI-Native Full Stack Developer Assignment</span>
        <span className="sep">·</span>
        <span className="muted-inline">
          Candidate: Murtaza Zaidi (zaidimurtaza102@gmail.com)
        </span>
      </div>
    </aside>
  );
}
