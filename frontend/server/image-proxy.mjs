// On-the-fly image resizing/compression cache. The CMS backend (PHP) stores whatever
// the admin panel uploads as-is — real originals here run 8-10MB, straight off a
// phone/camera, served completely unresized even where the page only shows a small
// thumbnail. That's most of "pages load slowly" for anything image-heavy (galleries,
// news, leader photos): the browser downloads megabytes for a few hundred on-screen
// pixels. This module fetches the original once, resizes/compresses it with sharp to a
// small fixed set of widths, and caches the result — same pattern as
// telegram-media-cache.mjs, just for CMS-hosted photos instead of Telegram ones.
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const rootDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const cacheDir = resolve(rootDir, "data", "image-cache");

// Only ever fetch from origins this site itself actually uploads to — an open "fetch
// any URL I give you" proxy is an SSRF/abuse vector, so this allowlist is not optional.
const ALLOWED_ORIGINS = [
  "https://api.fermi.uz",
  "https://fjsti.uz",
  "https://www.fjsti.uz",
  // fermi.uz itself (same-origin /media/ now that Django is behind it) and
  // beta.fermi.uz, the pre-cutover test subdomain — keep in sync with
  // src/lib/imageProxy.ts's mirrored list.
  "https://fermi.uz",
  "https://www.fermi.uz",
  "https://beta.fermi.uz",
  // Imported Telegram-channel media is hosted here. This remains a single,
  // explicit CDN origin rather than opening the proxy to arbitrary URLs.
  "https://cdn4.telesco.pe",
  // Django media host — keep in sync with src/lib/imageProxy.ts's mirrored list.
  "http://127.0.0.1:8000",
  "http://localhost:8000",
];
// Django's build_absolute_uri() (see production-server.mjs's streamProxy,
// which forwards X-Forwarded-Host precisely so this happens) always returns
// media URLs on the public domain, since that's what the browser needs — but
// this proxy runs on the same box as Django and fetching that same public
// URL back out is a same-server "hairpin" request, which many hosts' network
// setups refuse even though the public domain works fine for everyone else.
// Rewriting these specific origins to the internal Django origin before
// fetching sidesteps that entirely instead of depending on it happening to work.
const SELF_ORIGINS = ["https://fermi.uz", "https://www.fermi.uz", "https://beta.fermi.uz"];
// A small fixed set rather than arbitrary integers — keeps the cache bounded and closes
// off "request 10,000 different widths" as a cheap way to fill the disk.
const ALLOWED_WIDTHS = [200, 320, 480, 640, 900, 1200, 1600];
const MAX_SOURCE_BYTES = 30 * 1024 * 1024; // guards memory use against an unexpectedly huge upload
const MAX_AGE_MS = 90 * 24 * 60 * 60 * 1000; // stale cache entries are pruned after ~3 months
const CACHE_CONTROL = "public, max-age=2592000, immutable";

function ensureCacheDir() {
  if (!existsSync(cacheDir)) mkdirSync(cacheDir, { recursive: true });
}

function isAllowedSource(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    return ALLOWED_ORIGINS.includes(parsed.origin);
  } catch {
    return false;
  }
}

function cacheKeyFor(src, width, format) {
  // Bump the transform version when encoder settings change so an older,
  // larger cached WebP is never returned after a quality improvement.
  return createHash("sha1").update(`${src}|w${width}|${format}|q76`).digest("hex");
}

// Rewriting the URL alone isn't enough: Django's USE_X_FORWARDED_HOST +
// SECURE_PROXY_SSL_HEADER (see config/settings.py) mean a fetch straight to
// the internal gunicorn port with a bare Host header gets rejected as
// DisallowedHost (or SSL-redirected) exactly like any other direct hit on
// that port would. production-server.mjs's own streamProxy already forwards
// these two headers for the same reason -- see its comment on X-Forwarded-Host.
function resolveFetchTarget(src, fermiApiBaseUrl) {
  const parsed = new URL(src);
  if (!SELF_ORIGINS.includes(parsed.origin)) return { url: src, headers: {} };
  return {
    url: new URL(`${parsed.pathname}${parsed.search}`, fermiApiBaseUrl).toString(),
    headers: { "x-forwarded-host": parsed.host, "x-forwarded-proto": "https" },
  };
}

async function resizeAndCache(src, width, format, fermiApiBaseUrl) {
  const { url: fetchUrl, headers } = resolveFetchTarget(src, fermiApiBaseUrl);
  const upstream = await fetch(fetchUrl, { headers, signal: AbortSignal.timeout(20_000) });
  if (!upstream.ok) return null;
  const contentType = upstream.headers.get("content-type") || "";
  const buffer = Buffer.from(await upstream.arrayBuffer());
  if (buffer.length > MAX_SOURCE_BYTES) return null;

  // Animated formats would lose their animation through sharp's still-image pipeline —
  // simplest safe behavior is to pass those through unresized rather than break them.
  if (contentType.includes("gif") || contentType.includes("svg")) {
    return { buffer, contentType: contentType || "application/octet-stream" };
  }

  const resized = sharp(buffer).resize({ width, withoutEnlargement: true });
  // A PNG with real transparency needs to stay PNG (JPEG has no alpha channel), but a
  // huge share of "PNG" uploads here are actually plain photos someone exported/saved
  // as PNG with no alpha at all — PNG's lossless compression barely helps on
  // photographic detail, so those came out only marginally smaller than the original
  // (one real example: a 2.1MB opaque PNG stayed ~600KB after just resizing as PNG).
  // Checking hasAlpha and only keeping PNG when actually needed gets the same ~10-20x
  // win JPEG sources already get.
  const needsAlpha = contentType.includes("png") && (await sharp(buffer).metadata()).hasAlpha;

  let pipeline;
  let outContentType;
  if (needsAlpha) {
    // WebP preserves transparency and is substantially smaller than PNG for
    // the CMS posters used on the homepage. Keep PNG as a fallback for older
    // clients that do not advertise WebP support.
    if (format === "webp") {
      pipeline = resized.webp({ quality: 76, effort: 4 });
      outContentType = "image/webp";
    } else {
      pipeline = resized.png({ compressionLevel: 9 });
      outContentType = "image/png";
    }
  } else if (format === "webp") {
    pipeline = resized.webp({ quality: 76, effort: 4 });
    outContentType = "image/webp";
  } else {
    // Default to JPEG output — covers jpeg sources (the vast majority here), opaque
    // PNGs (see above), and any ambiguous/missing content-type. mozjpeg at quality 85
    // is visually near-lossless at the display sizes these are actually shown at.
    pipeline = resized.jpeg({ quality: 85, mozjpeg: true });
    outContentType = "image/jpeg";
  }
  const out = await pipeline.toBuffer();
  return { buffer: out, contentType: outContentType };
}

function purgeOldFiles() {
  try {
    ensureCacheDir();
    const now = Date.now();
    for (const name of readdirSync(cacheDir)) {
      const full = resolve(cacheDir, name);
      try {
        if (now - statSync(full).mtimeMs > MAX_AGE_MS) unlinkSync(full);
      } catch {
        /* removed concurrently — fine */
      }
    }
  } catch (error) {
    console.error("image-proxy: purge failed", error);
  }
}

let purgeStarted = false;
function ensurePurgeScheduled() {
  if (purgeStarted) return;
  purgeStarted = true;
  purgeOldFiles();
  const timer = setInterval(purgeOldFiles, 24 * 60 * 60 * 1000);
  timer.unref?.();
}

const ROUTE_PREFIX = "/img-cache";

export async function handleImageProxyRequest(request, response, fermiApiBaseUrl) {
  const requestUrl = new URL(request.url || "/", "http://localhost");
  if (!requestUrl.pathname.startsWith(ROUTE_PREFIX)) return false;
  ensurePurgeScheduled();

  const src = requestUrl.searchParams.get("src") || "";
  const width = Number(requestUrl.searchParams.get("w"));
  const format = String(request.headers.accept || "").includes("image/webp") ? "webp" : "legacy";

  if (!isAllowedSource(src) || !ALLOWED_WIDTHS.includes(width)) {
    response.statusCode = 400;
    response.end();
    return true;
  }

  ensureCacheDir();
  const key = cacheKeyFor(src, width, format);
  const metaPath = resolve(cacheDir, `${key}.json`);
  const dataPath = resolve(cacheDir, `${key}.bin`);

  if (existsSync(metaPath) && existsSync(dataPath)) {
    try {
      const meta = JSON.parse(readFileSync(metaPath, "utf8"));
      response.statusCode = 200;
      response.setHeader("Content-Type", meta.contentType);
      response.setHeader("Cache-Control", CACHE_CONTROL);
      response.setHeader("Vary", "Accept");
      response.end(readFileSync(dataPath));
      return true;
    } catch {
      /* fall through and regenerate */
    }
  }

  try {
    const result = await resizeAndCache(src, width, format, fermiApiBaseUrl);
    if (!result) {
      response.statusCode = 502;
      response.end();
      return true;
    }
    writeFileSync(dataPath, result.buffer);
    writeFileSync(metaPath, JSON.stringify({ contentType: result.contentType }));
    response.statusCode = 200;
    response.setHeader("Content-Type", result.contentType);
    response.setHeader("Cache-Control", CACHE_CONTROL);
    response.setHeader("Vary", "Accept");
    response.end(result.buffer);
  } catch (error) {
    console.error(`image-proxy: failed to process ${src} @ w${width}`, error);
    response.statusCode = 502;
    response.end();
  }
  return true;
}
