import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { MenuItem } from "../types";

/**
 * Renders the real site nav tree from /api/v1/menu/ instead of hardcoded
 * links — proves the Menu app is actually useful, not just an API that
 * nothing consumes. Uses uz labels for now; a global language context (as
 * opposed to each page's own local `lang` state) is the next piece needed
 * to make the whole nav language-aware, not just individual pages.
 */
export function MenuNav() {
  const [items, setItems] = useState<MenuItem[]>([]);

  useEffect(() => {
    fetch("/api/v1/menu/")
      .then((res) => res.json())
      .then(setItems)
      .catch(() => setItems([]));
  }, []);

  return (
    <div className="flex items-center gap-1">
      {items.map((item) => (
        <div key={item.id} className="group relative">
          {item.url ? (
            <Link
              to={item.url}
              className="rounded-lg px-3 py-1.5 text-sm font-semibold text-foreground-700 hover:bg-primary-50 hover:text-primary-800"
            >
              {item.label.uz}
            </Link>
          ) : (
            <span className="cursor-default rounded-lg px-3 py-1.5 text-sm font-semibold text-foreground-700 group-hover:bg-primary-50 group-hover:text-primary-800">
              {item.label.uz}
            </span>
          )}

          {item.children.length > 0 && (
            <div className="invisible absolute left-0 top-full z-10 min-w-48 rounded-xl border border-primary-100 bg-white py-1.5 opacity-0 shadow-lg transition-opacity group-hover:visible group-hover:opacity-100">
              {item.children.map((child) => (
                <Link
                  key={child.id}
                  to={child.url || "#"}
                  className="block px-4 py-2 text-sm text-foreground-700 hover:bg-primary-50 hover:text-primary-800"
                >
                  {child.label.uz}
                </Link>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
