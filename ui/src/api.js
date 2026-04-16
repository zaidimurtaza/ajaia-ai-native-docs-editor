import { apiBaseUrl } from "./config.js";

const apiPrefix = () => apiBaseUrl();

function qsShare(shareToken) {
  if (!shareToken) return "";
  return `?share_token=${encodeURIComponent(shareToken)}`;
}

async function req(path, opts = {}) {
  const headers = new Headers(opts.headers);
  if (!(opts.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (opts.token) headers.set("Authorization", `Bearer ${opts.token}`);
  const r = await fetch(`${apiPrefix()}${path}`, { ...opts, headers });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(text || r.statusText);
  }
  if (r.status === 204) return undefined;
  if (r.headers.get("content-length") === "0") return undefined;
  return r.json();
}

export async function login(email, password) {
  return req("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function listDocuments(token) {
  return req("/api/documents", { token });
}

export async function createDocument(token, title) {
  return req("/api/documents", {
    method: "POST",
    body: JSON.stringify({ title }),
    token,
  });
}

export async function getDocument(token, id, shareToken) {
  if (!token && !shareToken) throw new Error("Need session or share link");
  return req(`/api/documents/${id}${qsShare(shareToken)}`, {
    token: token ?? undefined,
  });
}

export async function getDocumentByLink(shareToken) {
  return req(`/api/documents/link/${encodeURIComponent(shareToken)}`, {});
}

export async function renameDocument(token, id, title) {
  return req(`/api/documents/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
    token,
  });
}

export async function getDocumentContent(token, id, shareToken) {
  if (!token && !shareToken) throw new Error("Need session or share link");
  return req(`/api/documents/${id}/content${qsShare(shareToken)}`, {
    token: token ?? undefined,
  });
}

export async function getContentByLink(shareToken) {
  return req(`/api/documents/link/${encodeURIComponent(shareToken)}/content`, {});
}

export async function putDocumentContent(token, id, content, shareToken) {
  if (!token && !shareToken) throw new Error("Need session or share link");
  return req(`/api/documents/${id}/content${qsShare(shareToken)}`, {
    method: "PUT",
    body: JSON.stringify({ content }),
    token: token ?? undefined,
  });
}

export async function putContentByLink(shareToken, content) {
  return req(`/api/documents/link/${encodeURIComponent(shareToken)}/content`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}

export async function listUsers(token) {
  return req("/api/documents/users", { token });
}

export async function shareDocument(token, docId, email, role) {
  return req(`/api/documents/${docId}/share`, {
    method: "POST",
    body: JSON.stringify({ email, role }),
    token,
  });
}

export async function createShareLink(token, docId, role) {
  return req(`/api/documents/${docId}/share-link`, {
    method: "POST",
    body: JSON.stringify({ role }),
    token,
  });
}

export async function revokeShareLink(token, docId) {
  await req(`/api/documents/${docId}/share-link`, {
    method: "DELETE",
    token,
  });
}

export async function importText(token, file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${apiPrefix()}/api/documents/import/text`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/** Replace open document body from UTF-8 .txt / .md / .markdown (clears saved editor JSON). */
export async function importTextIntoDocument(token, docId, file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${apiPrefix()}/api/documents/${docId}/import-body`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function listAttachments(token, docId, shareToken) {
  if (!token && !shareToken) throw new Error("Need session or share link");
  return req(`/api/documents/${docId}/attachments${qsShare(shareToken)}`, {
    token: token ?? undefined,
  });
}

export async function uploadAttachment(token, docId, file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${apiPrefix()}/api/documents/${docId}/attachments`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function downloadAttachment(token, docId, attachmentId, filename, shareToken) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const r = await fetch(
    `${apiPrefix()}/api/documents/${docId}/attachments/${attachmentId}/download${qsShare(shareToken)}`,
    { headers },
  );
  if (!r.ok) throw new Error(await r.text());
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
