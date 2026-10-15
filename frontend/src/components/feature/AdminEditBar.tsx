import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { me } from "@/api/auth";
import { apiClient } from "@/api/client";

interface Shortcut {
  to: string;
  label: string;
  icon: string;
  hint?: string;
}

interface Located {
  found: boolean;
  kind?: "news" | "faculty" | "department" | "page";
  title?: string;
  edit?: string;
}

/** Public routes whose last segment is the slug of the page being shown. */
const SLUG_ROUTES = /^\/(blog|faculty|departments|documents|news|detail|about)\//;

const HOME: Shortcut[] = [
  { to: "/admin/site-texts?q=hero", label: "Sarlavha va tugma yozuvlari", icon: "ri-translate-2" },
  { to: "/admin/home-tools", label: "Yuqoridagi tezkor tugmalar", icon: "ri-flashlight-line" },
  { to: "/admin/home-partners", label: "Hamkorlar", icon: "ri-links-line" },
  { to: "/admin/home-projects", label: "Bizning loyihalar", icon: "ri-stack-line" },
  { to: "/admin/home-voices", label: "Talabalar fikri", icon: "ri-user-voice-line" },
  { to: "/admin/home-facts", label: "Raqamlar", icon: "ri-bar-chart-line" },
  { to: "/admin/home-why", label: "Nega bizni tanlashadi", icon: "ri-award-line" },
  { to: "/admin/news", label: "Yangiliklar", icon: "ri-newspaper-line" },
  { to: "/admin/leaders", label: "Rahbariyat", icon: "ri-team-line" },
  { to: "/admin/gallery-images", label: "Foto galereya", icon: "ri-image-line" },
  { to: "/admin/counter", label: "Talabalar soni (hisoblagich)", icon: "ri-bar-chart-line" },
];

/** What an editor may want to change on the page they are looking at, besides the page's own text. */
function shortcutsFor(pathname: string): Shortcut[] {
  if (pathname === "/") return HOME;
  if (pathname.startsWith("/yangiliklar")) return [{ to: "/admin/news", label: "Yangiliklar ro'yxati", icon: "ri-newspaper-line" }];
  if (pathname.startsWith("/galereya") || pathname.startsWith("/full-gallery")) return [{ to: "/admin/gallery-images", label: "Foto galereya", icon: "ri-image-line" }];
  if (pathname.startsWith("/video")) return [{ to: "/admin/videos", label: "Videolar", icon: "ri-video-line" }];
  if (pathname.startsWith("/schedule")) return [{ to: "/admin/schedules", label: "Dars jadvali", icon: "ri-calendar-line" }];
  if (pathname.startsWith("/leader/")) return [{ to: "/admin/leaders", label: "Rahbariyat", icon: "ri-team-line" }];
  if (pathname.startsWith("/aloqa"))
    return [
      { to: "/admin/setting", label: "Telefon, email, manzil", icon: "ri-settings-3-line" },
      { to: "/admin/connect-leaders", label: "Aloqa mas'ullari", icon: "ri-contacts-line" },
      { to: "/admin/contacts", label: "Kelgan xabarlar", icon: "ri-mail-line" },
    ];
  if (pathname.startsWith("/qabul-natijalari"))
    return [
      { to: "/admin/result-files", label: "Natija fayllari", icon: "ri-file-pdf-2-line" },
      { to: "/admin/result-categories", label: "Yo'nalishlar", icon: "ri-list-check-2" },
    ];
  if (pathname.startsWith("/qabul")) return [{ to: "/admin/acceptances", label: "Kelgan arizalar", icon: "ri-file-edit-line" }];
  return [];
}

/** A small pencil in the corner of the public site, shown only to a signed-in administrator: opens the editor of the
 *  page being viewed (and the usual lists for that kind of page) instead of hunting through the admin menu. */
export default function AdminEditBar() {
  const { pathname } = useLocation();
  const [isAdmin, setIsAdmin] = useState(false);
  const [open, setOpen] = useState(false);
  const [located, setLocated] = useState<Located | null>(null);

  useEffect(() => {
    let cancelled = false;
    me()
      .then((user) => {
        if (!cancelled) setIsAdmin(user.role === "admin");
      })
      .catch(() => {
        if (!cancelled) setIsAdmin(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const slug = useMemo(() => (SLUG_ROUTES.test(pathname) ? decodeURIComponent(pathname.split("/").filter(Boolean).pop() ?? "") : ""), [pathname]);

  // Which editor owns this page: asked only when the editor opens the pencil, so nothing extra loads for a plain visit.
  useEffect(() => {
    setOpen(false);
    setLocated(null);
  }, [pathname]);

  useEffect(() => {
    if (!open || !slug || located) return;
    let cancelled = false;
    apiClient
      .get<Located>("admin/locate", { slug }, true)
      .then(({ data }) => {
        if (!cancelled) setLocated(data);
      })
      .catch(() => {
        if (!cancelled) setLocated({ found: false });
      });
    return () => {
      cancelled = true;
    };
  }, [open, slug, located]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!isAdmin || pathname.startsWith("/admin")) return null;

  const shortcuts = shortcutsFor(pathname);
  const KIND_LABEL: Record<string, string> = { news: "yangilikni", faculty: "fakultetni", department: "kafedrani", page: "sahifani" };

  return (
    <div className="fixed bottom-4 left-4 z-[60] print:hidden">
      {open && (
        <div role="menu" className="mb-2 w-72 max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border border-background-200 bg-background-50 shadow-2xl">
          <div className="border-b border-background-200 bg-primary-800 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-background-50/80">
            Admin: bu sahifani o'zgartirish
          </div>
          <ul className="max-h-[60vh] overflow-y-auto p-1.5 text-sm">
            {slug && (
              <li>
                {located === null ? (
                  <span className="flex items-center gap-2 px-3 py-2.5 text-foreground-500">
                    <i className="ri-loader-4-line animate-spin" aria-hidden="true" /> Qidirilmoqda...
                  </span>
                ) : located.found && located.edit ? (
                  <Link to={located.edit} role="menuitem" className="flex items-center gap-3 rounded-lg bg-secondary-100 px-3 py-2.5 font-semibold text-primary-900 hover:bg-secondary-200">
                    <i className="ri-pencil-line text-base" aria-hidden="true" />
                    <span className="min-w-0">
                      <span className="block">Shu {KIND_LABEL[located.kind ?? "page"]} tahrirlash</span>
                      {located.title && <span className="block truncate text-xs font-normal text-foreground-600">{located.title}</span>}
                    </span>
                  </Link>
                ) : (
                  <span className="block px-3 py-2.5 text-foreground-500">Bu sahifa uchun alohida muharrir topilmadi.</span>
                )}
              </li>
            )}
            {shortcuts.map((item) => (
              <li key={item.to}>
                <Link to={item.to} role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-foreground-800 hover:bg-background-100">
                  <i className={`${item.icon} text-base text-foreground-500`} aria-hidden="true" />
                  {item.label}
                </Link>
              </li>
            ))}
            <li className="mt-1 border-t border-background-200 pt-1">
              <Link to="/admin/site-texts" role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-foreground-800 hover:bg-background-100">
                <i className="ri-translate-2 text-base text-foreground-500" aria-hidden="true" />
                <span>
                  Saytdagi yozuvlarni o'zgartirish
                  <span className="block text-xs text-foreground-500">tugma, sarlavha, izoh matnlari</span>
                </span>
              </Link>
            </li>
            <li>
              <Link to="/admin/menu-tree" role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-foreground-800 hover:bg-background-100">
                <i className="ri-list-check-2 text-base text-foreground-500" aria-hidden="true" /> Menyu
              </Link>
            </li>
            <li>
              <Link to="/admin" role="menuitem" className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-foreground-800 hover:bg-background-100">
                <i className="ri-dashboard-line text-base text-foreground-500" aria-hidden="true" /> Admin panelga o'tish
              </Link>
            </li>
          </ul>
        </div>
      )}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex h-12 cursor-pointer items-center gap-2 rounded-full bg-primary-800 pl-4 pr-5 text-sm font-semibold text-background-50 shadow-xl ring-2 ring-secondary-500 hover:bg-primary-700"
      >
        <i className="ri-pencil-line text-lg text-secondary-500" aria-hidden="true" />
        Tahrirlash
      </button>
    </div>
  );
}
