import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchStatsSummary, type SiteStatsSummary } from "@/lib/siteStats";
import { useAdminAuth } from "../AdminAuthContext";
import { useAdminSummary } from "../dashboard";
import { formatDateTime } from "../format";
import { NAV_GROUPS } from "../nav";

const NUMBER = new Intl.NumberFormat("uz-UZ");

const QUICK = [
  { to: "/admin/news/new", label: "Yangilik qo'shish", hint: "Matn, rasm va tarjima bilan", icon: "ri-newspaper-line", primary: true },
  { to: "/admin/pages/new", label: "Sahifa qo'shish", hint: "Yangi matnli sahifa", icon: "ri-file-add-line", primary: false },
  { to: "/admin/gallery-images/new", label: "Rasm qo'shish", hint: "Foto galereyaga", icon: "ri-image-add-line", primary: false },
  { to: "/admin/menu-tree", label: "Menyuni tahrirlash", hint: "Saytning yuqori menyusi", icon: "ri-list-check-2", primary: false },
];

const INBOXES = NAV_GROUPS.find((group) => group.id === "inbox")?.items ?? [];

function greeting(): string {
  const hour = Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Asia/Tashkent", hour: "2-digit", hourCycle: "h23" }).format(new Date()));
  if (hour < 5) return "Xayrli tun";
  if (hour < 12) return "Xayrli tong";
  if (hour < 18) return "Xayrli kun";
  return "Xayrli kech";
}

const WEEKDAYS = ["yakshanba", "dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba"];
const MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"];

/** "14-oktabr, chorshanba" -- written out because browsers ship no Uzbek date names. */
function todayLabel(): string {
  const parts = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Tashkent", weekday: "short", day: "numeric", month: "numeric", year: "numeric" }).formatToParts(new Date());
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  const weekday = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(get("weekday"));
  return `${get("day")}-${MONTHS[Number(get("month")) - 1]} ${get("year")}, ${WEEKDAYS[weekday] ?? ""}`;
}

function Panel({ title, action, children }: { title: string; action?: { to: string; label: string }; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-background-200 bg-background-50">
      <div className="flex items-center justify-between gap-3 border-b border-background-200 px-5 py-3.5">
        <h2 className="font-heading text-sm font-bold text-foreground-900">{title}</h2>
        {action && (
          <Link to={action.to} className="text-xs font-semibold text-primary-600 hover:underline">
            {action.label}
          </Link>
        )}
      </div>
      {children}
    </section>
  );
}

export default function AdminDashboard() {
  const { user } = useAdminAuth();
  const { summary } = useAdminSummary();
  const [stats, setStats] = useState<SiteStatsSummary | null>(null);

  useEffect(() => {
    fetchStatsSummary()
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  const unreadTotal = summary ? Object.values(summary.unread).reduce((a, b) => a + b, 0) : 0;
  const trend = stats && stats.previous7Days > 0 ? Math.round(((stats.last7Days - stats.previous7Days) / stats.previous7Days) * 100) : null;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold text-foreground-950">
          {greeting()}, {user?.username}
        </h1>
        <p className="mt-1 text-sm text-foreground-500">{todayLabel()}</p>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {QUICK.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`flex items-center gap-3 rounded-xl border p-4 transition-colors ${
              item.primary
                ? "border-primary-500 bg-primary-500 text-background-50 hover:bg-primary-600"
                : "border-background-200 bg-background-50 text-foreground-900 hover:border-primary-300"
            }`}
          >
            <span
              className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-xl ${
                item.primary ? "bg-secondary-500 text-primary-950" : "bg-primary-50 text-primary-600"
              }`}
            >
              <i className={item.icon} aria-hidden="true" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold">{item.label}</span>
              <span className={`block truncate text-xs ${item.primary ? "text-background-50/70" : "text-foreground-500"}`}>{item.hint}</span>
            </span>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-5">
        <div className="space-y-5 lg:col-span-3">
          <Panel title="Murojaatlar" action={{ to: "/admin/contacts", label: "Barchasi" }}>
            {!summary ? (
              <p className="px-5 py-8 text-center text-sm text-foreground-500">Yuklanmoqda...</p>
            ) : (
              <>
                {unreadTotal === 0 && (
                  <div className="flex items-center gap-3 border-b border-background-200 bg-green-50 px-5 py-3 text-sm text-green-900">
                    <i className="ri-checkbox-circle-line text-lg text-green-600" aria-hidden="true" />
                    Hammasi ko'rilgan — yangi murojaat yo'q.
                  </div>
                )}
                <ul className="divide-y divide-background-200">
                  {INBOXES.map((item) => {
                    const count = summary.unread[item.badge ?? ""] ?? 0;
                    return (
                      <li key={item.to}>
                        <Link to={item.to} className="flex items-center gap-3 px-5 py-3 hover:bg-background-100">
                          <i className={`${item.icon} flex h-5 w-5 items-center justify-center text-base text-foreground-400`} aria-hidden="true" />
                          <span className="flex-1 text-sm text-foreground-800">{item.label}</span>
                          {count > 0 ? (
                            <span className="rounded-full bg-secondary-500 px-2.5 py-0.5 text-xs font-bold text-primary-950">{count} ta yangi</span>
                          ) : (
                            <span className="text-xs text-foreground-400">yangi yo'q</span>
                          )}
                          <i className="ri-arrow-right-s-line text-foreground-300" aria-hidden="true" />
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </Panel>

          <Panel title="So'nggi yangiliklar" action={{ to: "/admin/news", label: "Barchasi" }}>
            {!summary ? (
              <p className="px-5 py-8 text-center text-sm text-foreground-500">Yuklanmoqda...</p>
            ) : summary.news.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-foreground-500">Hali yangilik qo'shilmagan.</p>
            ) : (
              <ul className="divide-y divide-background-200">
                {summary.news.map((post) => (
                  <li key={post.id}>
                    <Link to={`/admin/news/${post.id}`} className="flex items-start gap-3 px-5 py-3 hover:bg-background-100">
                      <div className="min-w-0 flex-1">
                        <div className="line-clamp-2 text-sm font-medium text-foreground-900">{post.title}</div>
                        <div className="mt-0.5 text-xs text-foreground-500">{formatDateTime(post.published_at)}</div>
                      </div>
                      {post.hidden ? (
                        <span className="shrink-0 rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-800">Qoralama</span>
                      ) : (
                        <span className="flex shrink-0 items-center gap-1 text-xs text-foreground-500">
                          <i className="ri-eye-line" aria-hidden="true" /> {NUMBER.format(post.views)}
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>

        <div className="space-y-5 lg:col-span-2">
          <Panel title="Saytga tashriflar" action={{ to: "/admin/statistics", label: "Batafsil" }}>
            {!stats ? (
              <p className="px-5 py-8 text-center text-sm text-foreground-500">Yuklanmoqda...</p>
            ) : (
              <div className="grid grid-cols-2 gap-px bg-background-200">
                <div className="bg-background-50 px-5 py-4">
                  <div className="text-xs text-foreground-500">Bugun</div>
                  <div className="font-heading text-2xl font-bold tabular-nums text-foreground-950">{NUMBER.format(stats.today)}</div>
                  <div className="text-xs text-foreground-400">kecha: {NUMBER.format(stats.yesterday)}</div>
                </div>
                <div className="bg-background-50 px-5 py-4">
                  <div className="text-xs text-foreground-500">So'nggi 7 kun</div>
                  <div className="font-heading text-2xl font-bold tabular-nums text-foreground-950">{NUMBER.format(stats.last7Days)}</div>
                  {trend !== null && (
                    <div className={`text-xs font-medium ${trend >= 0 ? "text-green-700" : "text-red-600"}`}>
                      {trend >= 0 ? "▲" : "▼"} {Math.abs(trend)}% oldingi haftaga nisbatan
                    </div>
                  )}
                </div>
              </div>
            )}
          </Panel>

          {summary && summary.telegram_drafts > 0 && (
            <Link
              to="/admin/news?source=telegram"
              className="flex items-center gap-3 rounded-xl border border-primary-200 bg-primary-50 px-5 py-4 text-sm text-primary-900 hover:border-primary-300"
            >
              <i className="ri-telegram-line text-xl text-primary-600" aria-hidden="true" />
              <span className="flex-1">
                <b>Telegramdan {summary.telegram_drafts} ta yangilik</b> tasdiqingizni kutmoqda.
              </span>
              <i className="ri-arrow-right-s-line" aria-hidden="true" />
            </Link>
          )}

          {summary && summary.drafts > 0 && (
            <Link
              to="/admin/news"
              className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900 hover:border-amber-300"
            >
              <i className="ri-draft-line text-xl text-amber-600" aria-hidden="true" />
              <span className="flex-1">
                <b>{summary.drafts} ta qoralama</b> yangilik saytda ko'rinmayapti.
              </span>
              <i className="ri-arrow-right-s-line" aria-hidden="true" />
            </Link>
          )}

          <Link
            to="/admin/help"
            className="flex items-center gap-4 rounded-xl border border-background-200 bg-background-50 px-5 py-4 hover:border-primary-300"
          >
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-secondary-100 text-xl text-secondary-800">
              <i className="ri-question-line" aria-hidden="true" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold text-foreground-900">Qanday qilinadi?</span>
              <span className="block text-xs text-foreground-500">Yangilik, rasm, PDF qo'shish — qadam-baqadam qo'llanma</span>
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
