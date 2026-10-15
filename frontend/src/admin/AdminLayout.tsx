import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { apiClient } from "@/api/client";
import { logout } from "@/api/auth";
import { useAdminAuth } from "./AdminAuthContext";
import CommandPalette from "./components/CommandPalette";
import { ConfirmProvider } from "./components/ConfirmDialog";
import { ToastProvider } from "./components/Toast";
import type { AdminOutletContext, DashboardData } from "./dashboard";
import { groupOf, NAV_BOTTOM, NAV_GROUPS, NAV_TOP, type NavItem } from "./nav";

const OPEN_GROUPS_KEY = "fjsti-admin-open-groups";

function readOpenGroups(): string[] | null {
  try {
    const raw = window.localStorage.getItem(OPEN_GROUPS_KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    return Array.isArray(parsed) ? parsed.filter((v) => typeof v === "string") : null;
  } catch {
    return null;
  }
}

function writeOpenGroups(ids: string[]) {
  try {
    window.localStorage.setItem(OPEN_GROUPS_KEY, JSON.stringify(ids));
  } catch {
    /* private window / blocked storage: the menu just forgets its state */
  }
}

function SidebarLink({ item, count, onNavigate }: { item: NavItem; count?: number; onNavigate: () => void }) {
  return (
    <NavLink
      to={item.to}
      end={item.to === "/admin"}
      onClick={onNavigate}
      className={({ isActive }) =>
        `group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? "bg-background-50/15 text-background-50"
            : "text-background-50/70 hover:bg-background-50/10 hover:text-background-50"
        }`
      }
    >
      {({ isActive }) => (
        <>
          {isActive && <span className="absolute inset-y-1.5 left-0 w-1 rounded-r bg-secondary-500" aria-hidden="true" />}
          <i className={`${item.icon} flex h-5 w-5 shrink-0 items-center justify-center text-base`} aria-hidden="true" />
          <span className="flex-1 truncate">{item.label}</span>
          {count ? (
            <span className="min-w-5 rounded-full bg-secondary-500 px-1.5 text-center text-[11px] font-bold leading-5 text-primary-950">
              {count > 99 ? "99+" : count}
            </span>
          ) : null}
        </>
      )}
    </NavLink>
  );
}

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAdminAuth();

  const [menuOpen, setMenuOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [openGroups, setOpenGroups] = useState<string[]>(() => readOpenGroups() ?? ["work", "inbox"]);
  const [summary, setSummary] = useState<DashboardData | null>(null);

  const refreshSummary = useCallback(() => {
    apiClient
      .get<DashboardData>("admin/dashboard", undefined, true)
      .then(({ data }) => setSummary(data))
      .catch(() => {
        /* the badges are a convenience: without them the menu still works */
      });
  }, []);

  useEffect(() => {
    document.documentElement.classList.add("admin-shell");
    return () => document.documentElement.classList.remove("admin-shell");
  }, []);

  // Fresh numbers whenever the editor moves to another section (a message they just read must stop counting).
  useEffect(() => {
    refreshSummary();
  }, [location.pathname, refreshSummary]);

  // The section being worked in is always open, whatever was collapsed before.
  useEffect(() => {
    const id = groupOf(location.pathname);
    if (id) setOpenGroups((ids) => (ids.includes(id) ? ids : [...ids, id]));
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null;
      const typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(true);
      } else if (e.key === "/" && !typing) {
        e.preventDefault();
        setPaletteOpen(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function toggleGroup(id: string) {
    setOpenGroups((ids) => {
      const next = ids.includes(id) ? ids.filter((v) => v !== id) : [...ids, id];
      writeOpenGroups(next);
      return next;
    });
  }

  async function onLogout() {
    await logout();
    navigate("/admin/login");
  }

  const closeMenu = () => setMenuOpen(false);
  const totalUnread = summary ? Object.values(summary.unread).reduce((a, b) => a + b, 0) : 0;
  const context: AdminOutletContext = { summary, refreshSummary };

  return (
    <ToastProvider>
      <ConfirmProvider>
      <div className="min-h-screen bg-background-100 lg:flex">
        {menuOpen && <div className="fixed inset-0 z-40 bg-primary-950/50 lg:hidden" onClick={closeMenu} aria-hidden="true" />}

        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-primary-800 text-background-50 transition-transform duration-200 lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:w-64 lg:shrink-0 lg:translate-x-0 ${
            menuOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex h-16 shrink-0 items-center gap-3 border-b border-background-50/10 px-5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-secondary-500 text-sm font-extrabold text-primary-950">F</div>
            <div className="leading-tight">
              <div className="font-heading text-sm font-bold">FJSTI Admin</div>
              <div className="text-[11px] text-background-50/55">Boshqaruv paneli</div>
            </div>
            <button
              type="button"
              onClick={closeMenu}
              className="ml-auto flex h-9 w-9 cursor-pointer items-center justify-center rounded-md text-background-50/70 hover:bg-background-50/10 lg:hidden"
              aria-label="Menyuni yopish"
            >
              <i className="ri-close-line text-xl" />
            </button>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4" aria-label="Admin menyusi">
            {NAV_TOP.map((item) => (
              <SidebarLink key={item.to} item={item} onNavigate={closeMenu} />
            ))}

            <div className="space-y-1 pt-3">
              {NAV_GROUPS.map((group) => {
                const open = openGroups.includes(group.id);
                const groupUnread = group.items.reduce((sum, item) => sum + (item.badge ? summary?.unread[item.badge] ?? 0 : 0), 0);
                return (
                  <div key={group.id}>
                    <button
                      type="button"
                      onClick={() => toggleGroup(group.id)}
                      aria-expanded={open}
                      className="flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-background-50/55 transition-colors hover:text-background-50"
                    >
                      <span className="flex-1">{group.label}</span>
                      {!open && groupUnread > 0 && <span className="h-2 w-2 rounded-full bg-secondary-500" aria-label="Yangi murojaat bor" />}
                      <i className={`ri-arrow-down-s-line text-base transition-transform ${open ? "" : "-rotate-90"}`} aria-hidden="true" />
                    </button>
                    {open && (
                      <div className="space-y-0.5 pb-1">
                        {group.items.map((item) => (
                          <SidebarLink
                            key={item.to}
                            item={item}
                            count={item.badge ? summary?.unread[item.badge] : undefined}
                            onNavigate={closeMenu}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="space-y-0.5 border-t border-background-50/10 pt-3">
              {NAV_BOTTOM.map((item) => (
                <SidebarLink key={item.to} item={item} onNavigate={closeMenu} />
              ))}
            </div>
          </nav>

          <div className="shrink-0 border-t border-background-50/10 p-3">
            <div className="flex items-center gap-3 rounded-lg px-2 py-1.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-background-50/15 text-sm font-bold uppercase">
                {user?.username?.[0] ?? "?"}
              </div>
              <div className="min-w-0 flex-1 leading-tight">
                <div className="truncate text-sm font-semibold">{user?.username}</div>
                <div className="truncate text-[11px] text-background-50/55">{user?.email}</div>
              </div>
              <button
                type="button"
                onClick={onLogout}
                title="Chiqish"
                className="flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-md text-background-50/70 hover:bg-background-50/10 hover:text-background-50"
              >
                <i className="ri-logout-box-line text-lg" aria-hidden="true" />
                <span className="sr-only">Chiqish</span>
              </button>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b border-background-200 bg-background-50/95 px-3 backdrop-blur sm:gap-3 sm:px-6 lg:h-16">
            <button
              type="button"
              onClick={() => setMenuOpen(true)}
              className="relative flex h-10 w-10 cursor-pointer items-center justify-center rounded-md text-foreground-700 hover:bg-background-100 lg:hidden"
              aria-label="Menyuni ochish"
            >
              <i className="ri-menu-line text-xl" />
              {totalUnread > 0 && <span className="absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full bg-secondary-500 ring-2 ring-background-50" />}
            </button>

            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              className="flex h-10 min-w-0 flex-1 cursor-pointer items-center gap-2.5 rounded-lg border border-background-300 bg-background-100 px-3 text-left text-sm text-foreground-500 hover:border-primary-300 sm:max-w-md sm:flex-none sm:basis-96"
            >
              <i className="ri-search-line text-base" aria-hidden="true" />
              <span className="flex-1 truncate">Bo'limni qidirish...</span>
              <kbd className="hidden rounded border border-background-300 bg-background-50 px-1.5 py-0.5 text-[11px] text-foreground-500 sm:block">Ctrl K</kbd>
            </button>

            <div className="flex-1" />

            <Link
              to="/admin/news/new"
              className="hidden h-10 shrink-0 items-center gap-2 rounded-lg bg-primary-500 px-4 text-sm font-semibold text-background-50 hover:bg-primary-600 sm:flex"
            >
              <i className="ri-add-line" aria-hidden="true" /> Yangilik
            </Link>
            <a
              href="/"
              target="_blank"
              rel="noreferrer"
              className="flex h-10 shrink-0 items-center gap-2 rounded-lg border border-background-300 px-3 text-sm font-medium text-foreground-700 hover:bg-background-100"
            >
              <i className="ri-external-link-line" aria-hidden="true" />
              <span className="hidden sm:inline">Saytni ko'rish</span>
              <span className="sr-only sm:hidden">Saytni ko'rish</span>
            </a>
          </header>

          <main className="min-w-0 flex-1 px-4 py-5 sm:px-6 sm:py-7 lg:px-8">
            <Outlet context={context} />
          </main>
        </div>

        <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      </div>
      </ConfirmProvider>
    </ToastProvider>
  );
}
