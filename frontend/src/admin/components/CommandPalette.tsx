import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ALL_NAV_ITEMS, QUICK_ACTIONS, type NavItem } from "../nav";

interface Props {
  open: boolean;
  onClose: () => void;
}

/** Quick jump to any admin section: type a word ("rasm", "fakultet", "parol"), press Enter. */
export default function CommandPalette({ open, onClose }: Props) {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  const results = useMemo<NavItem[]>(() => {
    const q = query.trim().toLowerCase();
    const pool = [...QUICK_ACTIONS, ...ALL_NAV_ITEMS];
    if (!q) return pool.slice(0, 10);
    return pool.filter((item) => `${item.label} ${item.keywords ?? ""}`.toLowerCase().includes(q));
  }, [query]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActive(0);
    const t = window.setTimeout(() => inputRef.current?.focus(), 20);
    return () => window.clearTimeout(t);
  }, [open]);

  useEffect(() => setActive(0), [query]);

  if (!open) return null;

  function go(item: NavItem | undefined) {
    if (!item) return;
    onClose();
    navigate(item.to);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(results[active]);
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center bg-primary-950/50 px-4 pt-[12vh]" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-label="Bo'limni qidirish"
        className="w-full max-w-lg overflow-hidden rounded-xl border border-background-200 bg-background-50 shadow-2xl"
        onMouseDown={(e) => e.stopPropagation()}
        onKeyDown={onKeyDown}
      >
        <div className="flex items-center gap-3 border-b border-background-200 px-4">
          <i className="ri-search-line text-lg text-foreground-400" aria-hidden="true" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Qayerga o'tamiz? (masalan: rasm, fakultet, parol)"
            className="h-14 flex-1 bg-transparent text-sm text-foreground-900 focus:outline-none placeholder:text-foreground-400"
          />
          <kbd className="hidden rounded border border-background-300 px-1.5 py-0.5 text-[11px] text-foreground-500 sm:block">Esc</kbd>
        </div>
        <ul className="max-h-[50vh] overflow-y-auto p-2">
          {results.length === 0 && <li className="px-3 py-6 text-center text-sm text-foreground-500">Hech narsa topilmadi.</li>}
          {results.map((item, i) => (
            <li key={`${item.to}-${item.label}`}>
              <button
                type="button"
                onMouseEnter={() => setActive(i)}
                onClick={() => go(item)}
                className={`flex w-full cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm ${
                  i === active ? "bg-primary-50 text-primary-800" : "text-foreground-700"
                }`}
              >
                <i className={`${item.icon} flex h-5 w-5 items-center justify-center text-base`} aria-hidden="true" />
                <span className="flex-1">{item.label}</span>
                {i === active && <i className="ri-corner-down-left-line text-foreground-400" aria-hidden="true" />}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
