/**
 * A page opened before a deploy asks for script files (hashed names) that the new build no longer has. The fix is a
 * reload, which fetches the fresh index.html. It must not loop if the file is genuinely missing, so it is limited to
 * one reload per RELOAD_COOLDOWN_MS -- not one per browser session: a tab that stays open across several deploys
 * (the usual case while the site is being worked on) has to heal after every one of them.
 */
const KEY = "fermi-chunk-reload";
const RELOAD_COOLDOWN_MS = 30_000;

export function reloadForStaleBuild(): boolean {
  try {
    const last = Number(sessionStorage.getItem(KEY) || 0);
    if (last && Date.now() - last < RELOAD_COOLDOWN_MS) return false;
    sessionStorage.setItem(KEY, String(Date.now()));
    window.location.reload();
    return true;
  } catch {
    return false;
  }
}
