import { execFile } from "node:child_process";

/**
 * One request to Google's free translate endpoint, made with the `curl` program instead of Node's own `fetch`.
 * Why: on the production server the very same request answered 200 to curl and 429 ("too many requests") to Node's fetch
 * (Google tells the two apart by the way they open the connection), so every Telegram post stayed Uzbek in Russian and English.
 * Falls back to fetch when curl is not installed. Returns { status, body }; status 0 = the request could not be made.
 */
export function googleRequest(text, lang, { timeoutMs = 4000 } = {}) {
  const base = "https://translate.googleapis.com/translate_a/single";
  const query = { client: "gtx", sl: "uz", tl: lang, dt: "t", q: String(text).slice(0, 4500) };
  return new Promise((resolve) => {
    const args = ["-s", "--get", "-m", String(Math.ceil(timeoutMs / 1000)), "-A", "Mozilla/5.0 (compatible; FerMI-web/1.0)", "-w", "\n%{http_code}"];
    for (const [key, value] of Object.entries(query)) args.push("--data-urlencode", `${key}=${value}`);
    args.push(base);
    execFile("curl", args, { maxBuffer: 8 * 1024 * 1024, timeout: timeoutMs + 1500 }, async (error, stdout) => {
      if (error && error.code === "ENOENT") {
        // no curl on this machine: the plain fetch (it may be refused where curl is not)
        try {
          const url = new URL(base);
          for (const [key, value] of Object.entries(query)) url.searchParams.set(key, value);
          const response = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (compatible; FerMI-web/1.0)" }, signal: AbortSignal.timeout(timeoutMs) });
          resolve({ status: response.status, body: await response.text() });
        } catch {
          resolve({ status: 0, body: "" });
        }
        return;
      }
      const out = String(stdout || "");
      const cut = out.lastIndexOf("\n");
      const status = Number(out.slice(cut + 1)) || 0;
      resolve({ status, body: cut >= 0 ? out.slice(0, cut) : "" });
    });
  });
}
