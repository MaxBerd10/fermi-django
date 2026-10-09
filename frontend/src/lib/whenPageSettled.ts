/**
 * Runs `callback` once the page has finished loading and the browser has a spare moment (at the latest
 * `timeoutMs` after that). For work nobody is waiting for -- warming caches, loading a floating widget --
 * so it does not compete with what the visitor is looking at. Returns a function that cancels it.
 */
export function whenPageSettled(callback: () => void, timeoutMs = 4000): () => void {
  let cancelled = false;
  let idleId: number | undefined;
  let timerId: number | undefined;

  const run = () => {
    if (!cancelled) callback();
  };
  const afterLoad = () => {
    if (cancelled) return;
    if (typeof window.requestIdleCallback === "function") idleId = window.requestIdleCallback(run, { timeout: timeoutMs });
    else timerId = window.setTimeout(run, 2000);
  };

  if (document.readyState === "complete") afterLoad();
  else window.addEventListener("load", afterLoad, { once: true });

  return () => {
    cancelled = true;
    window.removeEventListener("load", afterLoad);
    if (idleId !== undefined) window.cancelIdleCallback?.(idleId);
    if (timerId !== undefined) window.clearTimeout(timerId);
  };
}
