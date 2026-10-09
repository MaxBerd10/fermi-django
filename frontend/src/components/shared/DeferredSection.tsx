import { Suspense, useEffect, useRef, useState, type ReactNode } from "react";

/**
 * Renders a part of a long page only when the visitor is about to reach it. Its code (when it is a lazy
 * component) and the data it fetches on mount then stay out of the first load, which on a phone competes
 * with what is actually on screen. `placeholderClassName` reserves roughly the section's height meanwhile
 * (sections below the first screen, so a slightly different real height moves nothing the visitor sees);
 * `id` keeps "#anchor" links working before the section exists.
 */
export default function DeferredSection({
  id,
  placeholderClassName,
  children,
  rootMargin = "1500px 0px",
}: {
  id?: string;
  placeholderClassName: string;
  children: ReactNode;
  rootMargin?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [near, setNear] = useState(false);

  useEffect(() => {
    if (near) return;
    const element = ref.current;
    if (!element || typeof IntersectionObserver === "undefined" || (id && window.location.hash === `#${id}`)) {
      setNear(true);
      return;
    }
    // a page opened on "#section" (or a link to it) must find the section, not an empty box
    const mountForHash = () => setNear(true);
    window.addEventListener("hashchange", mountForHash);
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) setNear(true);
      },
      { rootMargin },
    );
    observer.observe(element);
    return () => {
      observer.disconnect();
      window.removeEventListener("hashchange", mountForHash);
    };
  }, [near, rootMargin, id]);

  return (
    <div id={id} ref={ref} className={near ? undefined : placeholderClassName}>
      {near && <Suspense fallback={<div className={placeholderClassName} aria-hidden="true" />}>{children}</Suspense>}
    </div>
  );
}
