import i18n from "../i18n";
import type { ApiMeta } from "../types/api";
import { ApiError } from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

const ACCESS_TOKEN_KEY = "fjsti_access_token";
const REFRESH_TOKEN_KEY = "fjsti_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export interface ApiResult<T> {
  data: T;
  meta?: ApiMeta;
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  params?: Record<string, string | number | undefined | null>;
  body?: unknown;
  formData?: FormData;
  auth?: boolean;
  /** internal: prevents infinite refresh-retry loops */
  _isRetry?: boolean;
}

function activeLang(): "uz" | "ru" | "en" {
  const lang = (i18n.resolvedLanguage || i18n.language || "uz").slice(0, 2);
  return lang === "ru" || lang === "en" ? lang : "uz";
}

function buildUrl(path: string, params?: RequestOptions["params"]) {
  const url = new URL(BASE_URL.replace(/\/$/, "") + "/" + path.replace(/^\//, ""), window.location.origin);
  // Django ignores this (locale is resolved client-side, see resolveLocale
  // below), but harmless to keep sending — avoids touching every call site
  // that doesn't otherwise pass a `lang` param, and costs nothing server-side.
  url.searchParams.set("lang", activeLang());
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

/**
 * Our Django API returns every translated field as {uz, ru, en} rather than
 * resolving a locale server-side (the old Yii2 backend this client was built
 * against did the resolution itself, keyed off the `?lang=` param). This walks
 * a parsed response body and collapses any object whose keys are *exactly*
 * {uz, ru, en} down to the active language's value (falling back to uz if
 * that particular field is still missing a translation), recursing through
 * arrays and nested objects along the way. Applied once here, so every page
 * component downstream still just sees a plain string/array/whatever it
 * always expected — no `field[lang]` indexing scattered across ~40 call sites.
 *
 * This also flattens ContentBlock.data (itself {uz:{...}, ru:{...}, en:{...}})
 * in the same pass, so BlockRenderer can read block.data.text directly.
 */
const LOCALE_KEYS = ["uz", "ru", "en"] as const;

function resolveLocale<T>(value: unknown, lang: "uz" | "ru" | "en"): T {
  if (Array.isArray(value)) {
    return value.map((item) => resolveLocale(item, lang)) as T;
  }
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    const keys = Object.keys(obj);
    if (keys.length > 0 && keys.every((k) => (LOCALE_KEYS as readonly string[]).includes(k))) {
      return resolveLocale(obj[lang] ?? obj.uz, lang) as T;
    }
    const out: Record<string, unknown> = {};
    for (const key of keys) out[key] = resolveLocale(obj[key], lang);
    return out as T;
  }
  return value as T;
}

// Several homepage sections (Hero, Faculties, FacultiesNews, ContactMap...) each
// call getSettings()/listFaculty()/listDepartments() independently on mount —
// with no shared cache, that's several identical GET requests fired at the same
// instant, all competing for the same slow backend connection. This collapses
// concurrent identical GETs into one shared in-flight request (mirrors the same
// fix already applied server-side for iMentor in production-server.mjs).
// Deliberately no TTL/staleness cache beyond that — once a request settles, the
// next call always fetches fresh.
const inFlightGets = new Map<string, Promise<unknown>>();

/**
 * Reads a fetch Response shaped like Django REST Framework's actual output —
 * a plain JSON object for detail endpoints, or {count, next, previous, results}
 * for list endpoints (DRF's PageNumberPagination) — rather than the old Yii2
 * backend's {success, data, meta} / {success:false, error:{code,message}}
 * envelope. Errors come back as DRF's defaults too: {"detail": "..."} for
 * 401/403/404, or a {field: ["msg", ...]} dict for 400 validation errors.
 */
async function readDrfResponse<T>(response: Response, path: string): Promise<ApiResult<T>> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // No JSON body (e.g. a 204, or a proxy/network failure that isn't DRF at all)
  }

  if (!response.ok) {
    const errorBody = (body ?? {}) as Record<string, unknown>;
    const detail = errorBody.detail;
    const firstFieldMessage = Object.values(errorBody)
      .flat()
      .find((v): v is string => typeof v === "string");
    const message =
      typeof detail === "string" ? detail : firstFieldMessage ?? `Request to ${path} failed (${response.status})`;
    const fields = typeof detail === "string" ? undefined : (errorBody as Record<string, string[]>);
    throw new ApiError(message, String(response.status), response.status, fields);
  }

  const resolved = resolveLocale<unknown>(body, activeLang());

  if (
    resolved &&
    typeof resolved === "object" &&
    "results" in (resolved as Record<string, unknown>) &&
    "count" in (resolved as Record<string, unknown>)
  ) {
    const page = resolved as { results: T; count: number; next: string | null; previous: string | null };
    return { data: page.results, meta: { total: page.count, next: page.next, previous: page.previous } };
  }

  return { data: resolved as T };
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
  const url = buildUrl(path, options.params);
  const method = options.method || "GET";
  const dedupeKey = method === "GET" ? url : null;

  if (dedupeKey) {
    const pending = inFlightGets.get(dedupeKey);
    if (pending) return pending as Promise<ApiResult<T>>;
  }

  const doRequest = async (): Promise<ApiResult<T>> => {
    const headers: Record<string, string> = {};
    let body: BodyInit | undefined;

    if (options.formData) {
      body = options.formData;
    } else if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }

    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, { method, headers, body });

    try {
      return await readDrfResponse<T>(response, path);
    } catch (err) {
      if (
        err instanceof ApiError &&
        err.status === 401 &&
        options.auth &&
        !options._isRetry
      ) {
        const refreshed = await tryRefresh();
        if (refreshed) {
          return request<T>(path, { ...options, _isRetry: true });
        }
        clearTokens();
      }
      throw err;
    }
  };

  const resultPromise = doRequest();
  if (dedupeKey) {
    inFlightGets.set(dedupeKey, resultPromise);
    // `.finally()` returns its OWN derived promise, which nothing here awaits
    // or attaches a `.catch()` to — when `resultPromise` rejects (any failed
    // GET, e.g. a 404), that derived promise becomes a second, completely
    // unhandled rejection, regardless of whether the real caller (below)
    // properly catches `resultPromise` itself. The `.catch(() => {})` only
    // silences that internal bookkeeping chain; the actual `resultPromise`
    // returned to callers is untouched and still rejects normally for them.
    resultPromise
      .finally(() => {
        if (inFlightGets.get(dedupeKey) === resultPromise) inFlightGets.delete(dedupeKey);
      })
      .catch(() => {});
  }
  return resultPromise;
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const res = await request<{ accessToken: string; refreshToken: string }>("auth/refresh", {
      method: "POST",
      body: { refreshToken },
    });
    setTokens(res.data.accessToken, res.data.refreshToken);
    return true;
  } catch {
    return false;
  }
}

export const apiClient = {
  get: <T>(path: string, params?: RequestOptions["params"], auth = false) =>
    request<T>(path, { method: "GET", params, auth }),
  post: <T>(path: string, body?: unknown, auth = false) =>
    request<T>(path, { method: "POST", body, auth }),
  put: <T>(path: string, body?: unknown, auth = false) =>
    request<T>(path, { method: "PUT", body, auth }),
  del: <T>(path: string, auth = false) =>
    request<T>(path, { method: "DELETE", auth }),
  postForm: <T>(path: string, formData: FormData, auth = false) =>
    request<T>(path, { method: "POST", formData, auth }),
};
