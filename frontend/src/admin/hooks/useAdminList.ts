import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { adminResource } from "@/api/admin";
import { ApiError } from "@/types/api";

export function adminErrorMessage(err: unknown, fallback = "Xatolik yuz berdi. Qayta urinib ko'ring."): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return "Sessiya tugadi. Qaytadan kiring.";
    if (err.status === 403) return "Bu amal uchun ruxsat yo'q.";
    // The proxy in front of the API cuts requests over its body limit before Django sees them.
    if (err.status === 413) return "Fayl hajmi serverning ruxsat etilgan chegarasidan katta. Kichikroq fayl tanlang.";
    if (err.status >= 500) return "Serverda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.";
    return err.message || fallback;
  }
  return fallback;
}

/**
 * Shared list-page state for every admin resource (generic entities, news, pages).
 * Three near-identical copies of this used to live in GenericListPage/NewsListPage/
 * PagesListPage and shared the same bugs:
 *  - submitting a search from page 2+ fired TWO loads (one with the stale page, one
 *    after the page reset) and whichever answered last won, so the list could show
 *    the wrong page of results -- every load now carries a ticket and only the newest
 *    one may write state;
 *  - a failed load (e.g. a 404/500) rendered the same "Hech qanday yozuv topilmadi"
 *    as a genuinely empty list -- failures now surface as an error message;
 *  - a failed delete (a protected foreign key, a 500) threw an unhandled rejection and
 *    the row simply stayed, with no explanation.
 */
export function useAdminList<T extends { id: number }>(resource: string, pageSize = 20) {
  const api = useMemo(() => adminResource<T>(resource), [resource]);
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const ticket = useRef(0);

  const load = useCallback(async () => {
    const mine = ++ticket.current;
    setLoading(true);
    setError("");
    try {
      const { items: rows, meta } = await api.list({ page, pageSize, search: search || undefined });
      if (mine !== ticket.current) return;
      setItems(rows);
      setTotal(meta?.total ?? rows.length);
    } catch (err) {
      if (mine !== ticket.current) return;
      setItems([]);
      setTotal(0);
      setError(adminErrorMessage(err, "Ro'yxatni yuklab bo'lmadi."));
    } finally {
      if (mine === ticket.current) setLoading(false);
    }
  }, [api, page, pageSize, search]);

  useEffect(() => {
    load();
  }, [load]);

  const submitSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      setPage(1);
      setSearch(searchInput.trim());
    },
    [searchInput],
  );

  const remove = useCallback(
    async (item: T, label: string): Promise<void> => {
      if (!window.confirm(`"${label}" yozuvini o'chirishni tasdiqlaysizmi?`)) return;
      try {
        await api.remove(item.id);
      } catch (err) {
        setError(adminErrorMessage(err, "O'chirib bo'lmadi."));
        return;
      }
      // Deleting the last row of a page > 1 would otherwise reload an empty page.
      if (items.length === 1 && page > 1) setPage(page - 1);
      else await load();
    },
    [api, items.length, load, page],
  );

  return { items, loading, error, page, setPage, total, pageSize, searchInput, setSearchInput, submitSearch, remove, reload: load };
}
