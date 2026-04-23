// Local dev:  VITE_API_URL is unset → hits http://localhost:8000 directly.
// Docker:     VITE_API_URL=/api is baked in at build time (Dockerfile ARG).
//             Nginx proxies /api/* → backend, stripping the /api prefix.
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function apiPost(path, body, token = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export async function apiGet(path, token = null, params = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const query = new URLSearchParams(params).toString();
  const url = `${API}${path}${query ? "?" + query : ""}`;
  const res = await fetch(url, { headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export async function apiDelete(path, token) {
  const res = await fetch(`${API}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}
