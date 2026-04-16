/** API HTTP origin (no trailing slash). Empty = same origin (Vite dev proxy). */
export function apiBaseUrl() {
  const b = import.meta.env.VITE_API_BASE_URL?.trim();
  return b ? b.replace(/\/$/, "") : "";
}
