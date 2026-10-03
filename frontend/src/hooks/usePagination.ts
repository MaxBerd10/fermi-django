import { useCallback, useEffect, useMemo, useState, type RefObject } from "react";

/**
 * Client-side paging of an already-loaded list. The page snaps back to 1 whenever `resetKey` changes (a new
 * search, sort or subject) and is clamped if the list shrinks. `go()` also scrolls `scrollRef` into view so the
 * reader lands at the top of the new page instead of staring at the old page's footer.
 */
export function usePagination<T>(
  items: readonly T[] | null | undefined,
  pageSize: number,
  resetKey: string | number | null | undefined = "",
  scrollRef?: RefObject<HTMLElement | null>,
) {
  const [page, setPage] = useState(1);
  const total = items?.length ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages);

  useEffect(() => {
    setPage(1);
  }, [resetKey]);

  const pageItems = useMemo(
    () => (items ? items.slice((safePage - 1) * pageSize, safePage * pageSize) : []),
    [items, safePage, pageSize],
  );

  const go = useCallback(
    (next: number) => {
      setPage(Math.min(Math.max(1, next), totalPages));
      scrollRef?.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    },
    [totalPages, scrollRef],
  );

  return { page: safePage, totalPages, pageItems, offset: (safePage - 1) * pageSize, go };
}
