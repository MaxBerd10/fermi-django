// A short-lived in-memory copy of the public, read-only API answers (menu, pages, news list, ...), so a
// visitor does not wait for Django + the database on every page view.
//
// What it is careful about:
//  * only GET answers of an allowlist of public endpoints are kept -- never /auth, /admin, forms, search,
//    and not a single news article (opening one counts a view in Django, a cached copy would stop the count);
//  * a request that carries a sign-in token, or that asks for an HTML page (DRF's browsable API), is never
//    answered from the copy;
//  * only 200 answers are kept; cookies are never forwarded to Django or stored;
//  * fresh for 60 s; for the next 10 min the old copy is still sent at once while a new one is fetched in the
//    background (and it is also what is sent if Django is briefly down);
//  * any successful write that goes through this server (admin panel, django-admin) empties the whole cache,
//    so editors see their change on the very next load;
//  * the key includes the host (Django builds absolute media URLs from it), size is capped.

const FRESH_MS = 60_000;
const STALE_MS = 10 * 60_000;
const MAX_ENTRY_BYTES = 1_500_000;
const MAX_TOTAL_BYTES = 48_000_000;
const MAX_ENTRIES = 400;
const MAX_QUERY_LENGTH = 300;
const UPSTREAM_TIMEOUT_MS = 15_000;

const CACHEABLE_PATH =
  /^\/api\/v1\/(?:(?:menu|pages|faculties|departments|leaders|gallery|schedule|documents|video|districts|quarters)(?:\/[^/]+)*|news|settings|admission-results-page)\/?$/;

/** @type {Map<string, {at: number, status: number, headers: [string, string][], body: Buffer}>} */
const store = new Map();
const inflight = new Map();
let totalBytes = 0;
let generation = 0;

const DROPPED_HEADERS = new Set([
  "connection", "transfer-encoding", "content-encoding", "keep-alive", "content-length", "set-cookie",
]);

export function clearApiCache() {
  generation += 1;
  store.clear();
  inflight.clear();
  totalBytes = 0;
}

export function isCacheableApiGet(request, pathname, search) {
  if ((request.method || "GET") !== "GET") return false;
  if (!CACHEABLE_PATH.test(pathname)) return false;
  if (search.length > MAX_QUERY_LENGTH) return false;
  if (request.headers.authorization) return false;
  if (String(request.headers.accept || "").includes("text/html")) return false;
  return true;
}

function remember(key, entry) {
  const previous = store.get(key);
  if (previous) totalBytes -= previous.body.length;
  store.delete(key);
  store.set(key, entry);
  totalBytes += entry.body.length;
  while (store.size > MAX_ENTRIES || totalBytes > MAX_TOTAL_BYTES) {
    const oldest = store.keys().next().value;
    if (oldest === undefined) break;
    totalBytes -= store.get(oldest).body.length;
    store.delete(oldest);
  }
}

async function load(key, target, headers) {
  const started = generation;
  const upstream = await fetch(target, { method: "GET", headers, signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS) });
  const body = Buffer.from(await upstream.arrayBuffer());
  const result = {
    at: Date.now(),
    status: upstream.status,
    headers: [...upstream.headers].filter(([name]) => !DROPPED_HEADERS.has(name.toLowerCase())),
    body,
  };
  const isJson = String(upstream.headers.get("content-type") || "").includes("json");
  // `generation` moved on while this was fetched = something was edited meanwhile: use it once, do not keep it
  if (upstream.status === 200 && isJson && body.length <= MAX_ENTRY_BYTES && started === generation) remember(key, result);
  return result;
}

function send(response, entry, state) {
  response.statusCode = entry.status;
  for (const [name, value] of entry.headers) response.setHeader(name, value);
  response.setHeader("Content-Length", entry.body.length);
  response.setHeader("X-Fermi-Cache", state);
  response.end(entry.body);
}

/**
 * Answers the request from the cache (fetching from Django when needed). Returns false only when the request
 * is not eligible, so the caller proxies it as before.
 */
export async function serveCachedApiGet(request, response, baseUrl, requestUrl, upstreamHeaders) {
  if (!isCacheableApiGet(request, requestUrl.pathname, requestUrl.search)) return false;

  const host = String(request.headers.host || "");
  const key = `${host}|${requestUrl.pathname}${requestUrl.search}`;
  const target = new URL(`${requestUrl.pathname}${requestUrl.search}`, baseUrl);
  const headers = { ...upstreamHeaders, accept: "application/json", "accept-encoding": "identity" };
  delete headers.cookie;
  delete headers.authorization;
  if (host) headers["x-forwarded-host"] = host;

  const fetchOnce = () => {
    let pending = inflight.get(key);
    if (!pending) {
      pending = load(key, target, headers).finally(() => {
        if (inflight.get(key) === pending) inflight.delete(key);
      });
      inflight.set(key, pending);
    }
    return pending;
  };

  const entry = store.get(key);
  const age = entry ? Date.now() - entry.at : Infinity;
  if (entry && age < FRESH_MS) {
    remember(key, entry); // most recently used
    send(response, entry, "HIT");
    return true;
  }
  if (entry && age < STALE_MS) {
    fetchOnce().catch(() => {});
    send(response, entry, "STALE");
    return true;
  }
  try {
    send(response, await fetchOnce(), "MISS");
  } catch (error) {
    if (entry) return send(response, entry, "STALE-ERROR"), true;
    throw error;
  }
  return true;
}
