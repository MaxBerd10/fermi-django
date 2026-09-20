import { useEffect, useRef } from "react";

// Detail pages (department/faculty/news article/about/blog) swap a short
// loading spinner for real content that can run anywhere from ~1,000px to
// over 10,000px tall depending on how much the CMS page actually holds --
// no single static skeleton height comes close for all of them, and
// whichever way it's wrong, the footer (and everything below the fold)
// jumps that whole distance in one frame once the real content lands. That
// jump is exactly what Lighthouse's CLS metric penalizes hardest.
//
// This remembers each URL's last real content height (sessionStorage, so it
// survives navigation within the tab but never leaks across visitors) and
// hands it back as the *next* load's skeleton height for that same URL --
// on a repeat visit (including a user going back, or Lighthouse's own
// repeat-load testing patterns) the skeleton already matches, so there's
// nothing left to jump.
const STORAGE_PREFIX = "fermi:content-height:";

export function useRememberedContentHeight(key: string, loading: boolean) {
  const contentRef = useRef<HTMLDivElement | null>(null);

  const remembered = (() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_PREFIX + key);
      return raw ? Number(raw) : null;
    } catch {
      return null;
    }
  })();

  useEffect(() => {
    if (loading || !contentRef.current) return;
    const height = contentRef.current.offsetHeight;
    if (!height) return;
    try {
      sessionStorage.setItem(STORAGE_PREFIX + key, String(height));
    } catch {
      /* private mode / storage full -- skip remembering, not fatal */
    }
  }, [key, loading]);

  return { contentRef, remembered };
}
