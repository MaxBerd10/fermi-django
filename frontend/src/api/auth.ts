const ACCESS_KEY = "fermi_access";
const REFRESH_KEY = "fermi_refresh";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function parseJsonOrThrow(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

export async function register(username: string, email: string, password: string) {
  const res = await fetch("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  return parseJsonOrThrow(res);
}

export async function verifyEmail(uid: string, token: string) {
  const res = await fetch("/api/v1/auth/verify-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ uid, token }),
  });
  const data = await parseJsonOrThrow(res);
  setTokens(data.access, data.refresh);
  return data;
}

export async function login(username: string, password: string) {
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await parseJsonOrThrow(res);
  setTokens(data.access, data.refresh);
  return data;
}

export async function logout() {
  const refresh = localStorage.getItem(REFRESH_KEY);
  const access = getAccessToken();
  clearTokens();
  if (!refresh || !access) return;
  await fetch("/api/v1/auth/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${access}` },
    body: JSON.stringify({ refresh }),
  }).catch(() => {});
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
}

export async function me(): Promise<CurrentUser | null> {
  const access = getAccessToken();
  if (!access) return null;
  const res = await fetch("/api/v1/auth/me", { headers: { Authorization: `Bearer ${access}` } });
  if (!res.ok) {
    clearTokens();
    return null;
  }
  return res.json();
}
