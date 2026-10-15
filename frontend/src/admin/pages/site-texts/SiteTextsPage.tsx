import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { loadMessages } from "@/i18n/local/index";
import { listSiteTexts, saveSiteText, type SiteTextRow } from "@/api/adminSiteTexts";
import { normalizeUzbekApostrophes } from "@/lib/normalizeCmsText";
import { adminErrorMessage } from "@/admin/hooks/useAdminList";

type Lang = "uz" | "ru" | "en";
const LANGS: Lang[] = ["uz", "ru", "en"];
const PAGE_STEP = 40;

/** Names of the sections as an editor knows them; a section not listed here shows its key prefix. */
const SECTION_LABELS: Record<string, string> = {
  nav: "Menyu",
  hero: "Bosh sahifa: asosiy qism",
  footer: "Sahifa pastki qismi (footer)",
  common: "Umumiy yozuvlar",
  contact: "Aloqa (bosh sahifada)",
  aloqa: "Aloqa sahifasi",
  qabul: "Qabul",
  news: "Yangiliklar",
  events: "Tadbirlar",
  gallery: "Galereya",
  auth: "Kirish va ro'yxatdan o'tish",
  search: "Qidiruv",
  notFound: "Sahifa topilmadi",
  test: "Test bo'limi",
  keyslar: "Keyslar",
  catalog: "Test va keyslar katalogi",
  faculties: "Fakultetlar (bosh sahifa)",
  faculty: "Fakultet sahifasi",
  leader: "Rahbar sahifasi",
  leadership: "Rahbariyat (bosh sahifa)",
  partners: "Hamkorlar",
  whyUs: "Nega biz",
  voices: "Talabalar fikri",
  projects: "Loyihalarimiz",
  pathFinder: "Yo'nalish maslahatchisi",
  ai: "Yordamchi (chat) va maslahatchilar",
  vq: "Virtual qabulxona",
  stats: "Statistika",
  about: "Biz haqimizda",
  quickServices: "Tezkor xizmatlar",
  admission: "Qabul (abituriyentlar sahifalari)",
  admissionResults: "Qabul natijalari",
  contest: "Tanlov arizalari",
  region: "Viloyat, tuman",
  department: "Kafedra sahifasi",
  journal: "Jurnal",
  newspaper: "Gazeta",
  kongress: "Kongress",
  conference: "Konferensiyalar",
  council: "Ilmiy kengash",
};

/** Texts of the home-page lists that now live in their own editor (Bosh sahifa bloklari); editing them here would change nothing. */
const MOVED_TEXTS: { pattern: RegExp; label: string; to: string }[] = [
  { pattern: /^hero\.tools\.(vq|admit|path|test|hemis|contact)\./, label: "Tezkor tugmalar", to: "/admin/home-tools" },
  { pattern: /^hero\.tools\.(vq|admit|path|test|hemis|contact)\./, label: "Tezkor tugmalar", to: "/admin/home-tools" },
  { pattern: /^partners\.item\d+\./, label: "Hamkorlar", to: "/admin/home-partners" },
  { pattern: /^voices\.v\d+\.(quote|name|meta)$/, label: "Talabalar fikri", to: "/admin/home-voices" },
  { pattern: /^voices\.fact\d+\./, label: "Raqamlar", to: "/admin/home-facts" },
  { pattern: /^whyUs\.(item\d+\.(title|desc)|metric\d+)$/, label: "Nega bizni tanlashadi", to: "/admin/home-why" },
];
const movedTo = (key: string) => MOVED_TEXTS.find((entry) => entry.pattern.test(key));

const sectionOf = (key: string) => key.split(".")[0];
const labelOf = (section: string) => SECTION_LABELS[section] ?? section;

/** {{name}} placeholders: an edited text that loses one would show a blank where the value should be. */
function placeholders(text: string): string[] {
  return [...new Set((text.match(/\{\{[^}]+\}\}/g) ?? []).map((p) => p.replace(/\s+/g, "")))];
}

function missingPlaceholders(def: string, draft: string): string[] {
  if (!draft.trim()) return [];
  const present = new Set(placeholders(draft));
  return placeholders(def).filter((p) => !present.has(p));
}

export default function SiteTextsPage() {
  const [defaults, setDefaults] = useState<Record<Lang, Record<string, string>> | null>(null);
  const [overrides, setOverrides] = useState<Record<string, SiteTextRow>>({});
  const [loadError, setLoadError] = useState("");
  // /admin/site-texts?q=hero opens the page already filtered (links from the public-site editor bar)
  const [params] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [section, setSection] = useState("");
  const [onlyEdited, setOnlyEdited] = useState(false);
  const [limit, setLimit] = useState(PAGE_STEP);
  const [openKey, setOpenKey] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadMessages("uz"), loadMessages("ru"), loadMessages("en"), listSiteTexts()])
      .then(([uz, ru, en, rows]) => {
        // a few built-in values are numbers: everything here is handled as text
        const asText = (bundle: Record<string, unknown>) =>
          Object.fromEntries(Object.entries(bundle).map(([key, value]) => [key, typeof value === "string" ? value : String(value ?? "")]));
        setDefaults({ uz: asText(uz), ru: asText(ru), en: asText(en) });
        setOverrides(Object.fromEntries(rows.map((row) => [row.key, row])));
      })
      .catch((err) => setLoadError(adminErrorMessage(err, "Matnlarni yuklab bo'lmadi.")));
  }, []);

  const keys = useMemo(() => {
    if (!defaults) return [];
    const ordered = Object.keys(defaults.uz);
    const seen = new Set(ordered);
    for (const lang of ["ru", "en"] as const) for (const key of Object.keys(defaults[lang])) if (!seen.has(key)) (seen.add(key), ordered.push(key));
    return ordered;
  }, [defaults]);

  const sections = useMemo(() => {
    const counts = new Map<string, number>();
    for (const key of keys) counts.set(sectionOf(key), (counts.get(sectionOf(key)) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => labelOf(a[0]).localeCompare(labelOf(b[0]), "uz"));
  }, [keys]);

  const visible = useMemo(() => {
    if (!defaults) return [];
    const needle = query.trim().toLowerCase();
    return keys.filter((key) => {
      if (section && sectionOf(key) !== section) return false;
      if (onlyEdited && !overrides[key]) return false;
      if (!needle) return true;
      const own = overrides[key];
      const haystack = [key, defaults.uz[key], defaults.ru[key], defaults.en[key], own?.text_uz, own?.text_ru, own?.text_en];
      return haystack.some((value) => (value ?? "").toLowerCase().includes(needle));
    });
  }, [defaults, keys, query, section, onlyEdited, overrides]);

  useEffect(() => setLimit(PAGE_STEP), [query, section, onlyEdited]);

  function applySaved(key: string, saved: SiteTextRow & { deleted?: boolean }) {
    setOverrides((current) => {
      const next = { ...current };
      if (saved.deleted) delete next[key];
      else next[key] = saved;
      return next;
    });
  }

  return (
    <div className="max-w-5xl">
      <h1 className="font-heading text-2xl font-bold text-foreground-950 mb-2">Sayt matnlari</h1>
      <p className="text-sm text-foreground-600 mb-5">
        Saytdagi har bir yozuvni (tugma, sarlavha, bosh sahifa matni, pastki qism...) shu yerda uch tilda o'zgartirishingiz mumkin.
        Til maydonini bo'sh qoldirsangiz, shu til uchun asl matn saqlanadi. O'zgarish saytda bir necha soniyada ko'rinadi.
        Yangiliklar, sahifa ichidagi matnlar va rasmlar esa «Yangiliklar» va «Sahifalar» bo'limlarida tahrirlanadi.
      </p>

      {loadError && <div role="alert" className="mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-800">{loadError}</div>}
      {!defaults && !loadError && (
        <div className="py-16 flex justify-center">
          <i className="ri-loader-4-line animate-spin text-primary-500 text-3xl" />
        </div>
      )}

      {defaults && (
        <>
          <div className="mb-4 grid gap-2 sm:grid-cols-[1fr_260px_auto] items-center">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Matn yoki kalit bo'yicha qidirish..."
              className="h-10 px-4 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
            />
            <select
              value={section}
              onChange={(e) => setSection(e.target.value)}
              className="h-10 px-3 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
            >
              <option value="">Barcha bo'limlar ({keys.length})</option>
              {sections.map(([name, count]) => (
                <option key={name} value={name}>{labelOf(name)} ({count})</option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm text-foreground-700 cursor-pointer">
              <input type="checkbox" checked={onlyEdited} onChange={(e) => setOnlyEdited(e.target.checked)} />
              Faqat o'zgartirilganlar ({Object.keys(overrides).length})
            </label>
          </div>

          <p className="text-xs text-foreground-500 mb-3">{visible.length} ta matn topildi.</p>

          <div className="space-y-2">
            {visible.slice(0, limit).map((key) => (
              <TextRow
                key={key}
                textKey={key}
                defaults={defaults}
                override={overrides[key]}
                open={openKey === key}
                onToggle={() => setOpenKey(openKey === key ? null : key)}
                onSaved={(saved) => applySaved(key, saved)}
              />
            ))}
          </div>

          {visible.length > limit && (
            <button
              type="button"
              onClick={() => setLimit(limit + PAGE_STEP)}
              className="mt-4 h-10 px-5 rounded-md border border-background-300 text-sm font-medium hover:bg-background-100 cursor-pointer"
            >
              Yana ko'rsatish ({visible.length - limit})
            </button>
          )}
        </>
      )}
    </div>
  );
}

interface RowProps {
  textKey: string;
  defaults: Record<Lang, Record<string, string>>;
  override?: SiteTextRow;
  open: boolean;
  onToggle: () => void;
  onSaved: (saved: SiteTextRow & { deleted?: boolean }) => void;
}

function TextRow({ textKey, defaults, override, open, onToggle, onSaved }: RowProps) {
  const [draft, setDraft] = useState<Record<Lang, string>>({ uz: "", ru: "", en: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (open) {
      setDraft({ uz: override?.text_uz ?? "", ru: override?.text_ru ?? "", en: override?.text_en ?? "" });
      setError("");
      setSaved(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const moved = movedTo(textKey);
  const problems = LANGS.flatMap((lang) => {
    const missing = missingPlaceholders(defaults[lang][textKey] ?? "", draft[lang]);
    return missing.length ? [`${lang.toUpperCase()}: ${missing.join(", ")} qoldirilishi kerak (u o'rnida qiymat ko'rsatiladi)`] : [];
  });

  async function submit(clear: boolean) {
    if (!clear && problems.length) return;
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      const payload = clear
        ? { key: textKey, text_uz: "", text_ru: "", text_en: "" }
        : { key: textKey, text_uz: normalizeUzbekApostrophes(draft.uz), text_ru: draft.ru, text_en: draft.en };
      const result = await saveSiteText(payload);
      onSaved(result);
      if (clear) setDraft({ uz: "", ru: "", en: "" });
      setSaved(true);
    } catch (err) {
      setError(adminErrorMessage(err, "Saqlashda xatolik yuz berdi."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className={`rounded-lg border ${open ? "border-primary-400 bg-background-50" : "border-background-200 bg-background-50"}`}>
      <button type="button" onClick={onToggle} className="w-full text-left px-4 py-3 flex items-start gap-3 cursor-pointer" aria-expanded={open}>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-mono text-foreground-400 truncate">{textKey}</p>
          <p className="text-sm text-foreground-900 whitespace-pre-wrap break-words line-clamp-2">
            {override?.text_uz || defaults.uz[textKey] || defaults.ru[textKey] || defaults.en[textKey]}
          </p>
        </div>
        {moved && <span className="shrink-0 mt-0.5 px-2 py-0.5 rounded-full bg-background-200 text-foreground-700 text-[11px] font-semibold">Boshqa bo'limda</span>}
        {override && !moved && <span className="shrink-0 mt-0.5 px-2 py-0.5 rounded-full bg-primary-100 text-primary-700 text-[11px] font-semibold">O'zgartirilgan</span>}
        <i className={`ri-arrow-down-s-line text-lg text-foreground-400 transition-transform ${open ? "rotate-180" : ""}`} aria-hidden />
      </button>

      {open && moved && (
        <div className="px-4 pb-4 pt-3 border-t border-background-200 text-sm text-foreground-700">
          Bu matn endi alohida bo'limdan tahrirlanadi:{" "}
          <Link to={moved.to} className="font-semibold text-primary-600 underline hover:text-primary-700">
            Bosh sahifa bloklari → {moved.label}
          </Link>
          . U yerda qatorlarni qo'shish, o'chirish va tartibini o'zgartirish ham mumkin.
        </div>
      )}

      {open && !moved && (
        <div className="px-4 pb-4 pt-1 space-y-3 border-t border-background-200">
          {LANGS.map((lang) => (
            <div key={lang}>
              <label className="block text-xs font-semibold uppercase tracking-wide text-foreground-700 mb-1">{lang}</label>
              <textarea
                value={draft[lang]}
                onChange={(e) => setDraft((d) => ({ ...d, [lang]: e.target.value }))}
                rows={Math.min(8, Math.max(2, Math.ceil((draft[lang] || defaults[lang][textKey] || "").length / 90)))}
                placeholder={defaults[lang][textKey] ?? ""}
                className="w-full px-3 py-2 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              />
              <p className="mt-1 text-[11px] text-foreground-500 whitespace-pre-wrap break-words">
                Asl matn: {defaults[lang][textKey] || "(yo'q)"}
                {defaults[lang][textKey] && draft[lang] !== defaults[lang][textKey] && (
                  <button
                    type="button"
                    onClick={() => setDraft((d) => ({ ...d, [lang]: defaults[lang][textKey] }))}
                    className="ml-2 underline text-primary-600 hover:text-primary-700 cursor-pointer"
                  >
                    Asl matnni nusxalash
                  </button>
                )}
              </p>
            </div>
          ))}

          {problems.length > 0 && <div role="alert" className="p-2.5 rounded-md bg-red-50 border border-red-200 text-xs text-red-800">{problems.join(" · ")}</div>}
          {error && <div role="alert" className="p-2.5 rounded-md bg-red-50 border border-red-200 text-xs text-red-800">{error}</div>}
          {saved && <div role="status" className="p-2.5 rounded-md bg-green-50 border border-green-200 text-xs text-green-800">Saqlandi. Saytda bir necha soniyada ko'rinadi.</div>}

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={saving || problems.length > 0}
              onClick={() => submit(false)}
              className="h-10 px-5 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer disabled:opacity-50"
            >
              {saving ? "Saqlanmoqda..." : "Saqlash"}
            </button>
            {override && (
              <button
                type="button"
                disabled={saving}
                onClick={() => submit(true)}
                className="h-10 px-4 rounded-md border border-background-300 text-sm font-medium hover:bg-background-100 cursor-pointer disabled:opacity-50"
              >
                Asl matnga qaytarish
              </button>
            )}
            <button type="button" onClick={onToggle} className="h-10 px-4 rounded-md text-sm text-foreground-600 hover:bg-background-100 cursor-pointer">Yopish</button>
          </div>
        </div>
      )}
    </div>
  );
}
