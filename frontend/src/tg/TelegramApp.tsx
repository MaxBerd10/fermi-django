import { useCallback, useEffect, useRef, useState, type CSSProperties, type FormEvent, type ReactNode } from "react";
import { AppError, getMe, getSubmissions, register, submitNews, uploadPhoto, type Me, type Submission } from "./api";
import { close, confirmClosing, expand, initData, ready, theme } from "./bridge";
import { prepareImage } from "./image";

/**
 * The staff news form that opens inside Telegram (the bot's "Yangilik yuborish" button): pictures, title, text, send.
 * What is sent becomes a DRAFT in the admin panel; nothing is published without an administrator.
 * Server side: apps/telegram_bot/webapp.py. Colours follow the person's Telegram theme (light or dark).
 */
const FALLBACK = { bg: "#f4f5f9", card: "#ffffff", fg: "#0a0a0a", hint: "#6b7280", accent: "#0a1158", accentFg: "#ffffff", line: "rgba(120,120,128,0.25)" };

const palette: CSSProperties = {
  ["--bg" as string]: theme.secondary_bg_color || theme.bg_color || FALLBACK.bg,
  ["--card" as string]: theme.bg_color || FALLBACK.card,
  ["--fg" as string]: theme.text_color || FALLBACK.fg,
  ["--hint" as string]: theme.hint_color || FALLBACK.hint,
  ["--accent" as string]: theme.button_color || FALLBACK.accent,
  ["--accent-fg" as string]: theme.button_text_color || FALLBACK.accentFg,
  ["--line" as string]: FALLBACK.line,
};

const card = "rounded-2xl bg-[var(--card)] p-4 shadow-sm";
const input =
  "w-full rounded-xl border border-[var(--line)] bg-[var(--bg)] px-4 py-3 text-base text-[color:var(--fg)] outline-none focus:border-[var(--accent)]";
const primary =
  "flex h-12 w-full cursor-pointer items-center justify-center gap-2 rounded-xl bg-[var(--accent)] text-base font-semibold text-[color:var(--accent-fg)] disabled:opacity-50";
const ghost =
  "flex h-12 w-full cursor-pointer items-center justify-center gap-2 rounded-xl border border-[var(--line)] text-base font-medium text-[color:var(--fg)]";

function Screen({ children }: { children: ReactNode }) {
  return <div className="mx-auto flex min-h-screen max-w-md flex-col gap-4 px-4 pb-28 pt-5">{children}</div>;
}

function Notice({ tone, children }: { tone: "error" | "info" | "ok"; children: ReactNode }) {
  const style = { error: "bg-red-100 text-red-900", info: "bg-amber-100 text-amber-900", ok: "bg-green-100 text-green-900" }[tone];
  return <div role={tone === "error" ? "alert" : "status"} className={`rounded-xl px-4 py-3 text-sm leading-snug ${style}`}>{children}</div>;
}

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-baseline justify-between text-sm font-semibold text-[color:var(--fg)]">
        {label}
        {hint && <span className="text-xs font-normal text-[color:var(--hint)]">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

// --- registration ----------------------------------------------------------------------------------------------

function Register({ me, onDone }: { me: Me; onDone: (next: Me) => void }) {
  const [name, setName] = useState(me.telegram_name);
  const [department, setDepartment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onDone(await register(name, department));
    } catch (err) {
      setError(err instanceof AppError ? err.message : "Xatolik yuz berdi.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      <div>
        <h1 className="text-2xl font-bold text-[color:var(--fg)]">Tanishib olamiz</h1>
        <p className="mt-1 text-sm text-[color:var(--hint)]">FJSTI saytiga yangilik yuborish uchun ism va bo'limingizni yozing.</p>
      </div>
      <form onSubmit={submit} className={`${card} space-y-4`}>
        <Field label="Ism va familiya">
          <input className={input} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" required />
        </Field>
        <Field label="Bo'lim, kafedra yoki laboratoriya">
          <input className={input} value={department} onChange={(e) => setDepartment(e.target.value)} placeholder="Masalan: Ilmiy bo'lim" required />
        </Field>
        {error && <Notice tone="error">{error}</Notice>}
        <button type="submit" disabled={busy || name.trim().length < 3 || department.trim().length < 2} className={primary}>
          {busy ? "Yuborilmoqda..." : "Davom etish"}
        </button>
      </form>
      <Notice tone={me.invited ? "ok" : "info"}>
        {me.invited ? "Havola orqali kirdingiz: ro'yxatdan o'tishingiz bilan yangilik yubora olasiz." : "Ruxsatni admin beradi: so'rovingiz unga yuboriladi."}
      </Notice>
    </Screen>
  );
}

function Waiting({ me, onRefresh }: { me: Me; onRefresh: () => void }) {
  const blocked = me.status === "blocked";
  return (
    <Screen>
      <div className={`${card} space-y-3 text-center`}>
        <i className={`${blocked ? "ri-lock-line" : "ri-time-line"} text-5xl text-[color:var(--hint)]`} aria-hidden="true" />
        <h1 className="text-xl font-bold text-[color:var(--fg)]">{blocked ? "Ruxsat berilmagan" : "Ruxsat kutilmoqda"}</h1>
        <p className="text-sm text-[color:var(--hint)]">
          {blocked ? "Sizga yangilik yuborish uchun ruxsat berilmagan." : "So'rovingiz adminda ko'rib chiqilmoqda. Ruxsat berilgach botdan xabar keladi."}
        </p>
      </div>
      {!blocked && (
        <button type="button" onClick={onRefresh} className={ghost}>
          <i className="ri-refresh-line" aria-hidden="true" /> Tekshirish
        </button>
      )}
    </Screen>
  );
}

// --- home ------------------------------------------------------------------------------------------------------

const STATE_LABEL = {
  pending: { text: "Tasdiq kutmoqda", style: "bg-amber-100 text-amber-900", icon: "ri-time-line" },
  published: { text: "Saytda chiqdi", style: "bg-green-100 text-green-900", icon: "ri-checkbox-circle-line" },
  removed: { text: "Rad etildi", style: "bg-gray-200 text-gray-700", icon: "ri-close-circle-line" },
} as const;

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString("ru-RU", { timeZone: "Asia/Tashkent", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function Home({ me, onNew }: { me: Me; onNew: () => void }) {
  const [items, setItems] = useState<Submission[] | null>(null);
  const [error, setError] = useState("");
  const left = Math.max(0, me.limits.per_day - me.limits.sent_today);

  useEffect(() => {
    getSubmissions()
      .then(setItems)
      .catch((err) => setError(err instanceof AppError ? err.message : "Ro'yxatni yuklab bo'lmadi."));
  }, []);

  return (
    <Screen>
      <div>
        <p className="text-sm text-[color:var(--hint)]">Salom,</p>
        <h1 className="text-2xl font-bold text-[color:var(--fg)]">{me.full_name}</h1>
        <p className="text-sm text-[color:var(--hint)]">{me.department}</p>
      </div>

      <button type="button" onClick={onNew} disabled={left === 0} className={`${primary} h-14 text-lg`}>
        <i className="ri-add-line text-xl" aria-hidden="true" /> Yangi yangilik
      </button>
      <p className="-mt-2 text-center text-xs text-[color:var(--hint)]">
        {left === 0 ? "Bugungi chegaraga yetdingiz. Ertaga davom eting." : `Bugun yana ${left} ta yangilik yuborishingiz mumkin.`}
      </p>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[color:var(--hint)]">Mening yangiliklarim</h2>
        {error && <Notice tone="error">{error}</Notice>}
        {items === null && !error && <p className="text-sm text-[color:var(--hint)]">Yuklanmoqda...</p>}
        {items?.length === 0 && <div className={`${card} text-center text-sm text-[color:var(--hint)]`}>Hali yangilik yubormagansiz.</div>}
        {items?.map((item) => {
          const label = STATE_LABEL[item.state];
          return (
            <article key={item.id} className={`${card} flex gap-3`}>
              {item.thumb ? (
                <img src={item.thumb} alt="" className="h-16 w-16 shrink-0 rounded-xl object-cover" loading="lazy" />
              ) : (
                <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-[var(--bg)] text-2xl text-[color:var(--hint)]"><i className="ri-image-line" aria-hidden="true" /></div>
              )}
              <div className="min-w-0 flex-1">
                <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-[color:var(--fg)]">{item.title}</h3>
                <div className="mt-1.5 flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${label.style}`}>
                    <i className={label.icon} aria-hidden="true" /> {label.text}
                  </span>
                  <span className="text-xs text-[color:var(--hint)]">{formatDate(item.created_at)}</span>
                </div>
                {item.url && (
                  <a href={item.url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-[color:var(--accent)]">
                    Saytda ko'rish <i className="ri-external-link-line" aria-hidden="true" />
                  </a>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </Screen>
  );
}

// --- compose ---------------------------------------------------------------------------------------------------

interface Photo {
  key: number;
  preview: string;
  status: "uploading" | "done" | "error";
  path?: string;
  error?: string;
}

function Compose({ me, onBack, onSent }: { me: Me; onBack: () => void; onSent: () => void }) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState<number | null>(me.categories[0]?.id ?? null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const nextKey = useRef(1);

  const dirty = Boolean(title || body || photos.length);
  useEffect(() => {
    confirmClosing(dirty);
    return () => confirmClosing(false);
  }, [dirty]);

  const patch = useCallback((key: number, change: Partial<Photo>) => setPhotos((list) => list.map((p) => (p.key === key ? { ...p, ...change } : p))), []);

  async function sendOne(key: number, file: File) {
    try {
      const { blob, preview } = await prepareImage(file);
      if (preview) patch(key, { preview });
      const { path } = await uploadPhoto(blob);
      patch(key, { status: "done", path });
    } catch (err) {
      patch(key, { status: "error", error: err instanceof AppError ? err.message : "Yuklab bo'lmadi." });
    }
  }

  async function addFiles(list: FileList | null) {
    const chosen = Array.from(list ?? []).slice(0, Math.max(0, me.limits.photos - photos.length));
    if (fileInput.current) fileInput.current.value = "";
    const fresh = chosen.map((file) => ({ key: nextKey.current++, file }));
    setPhotos((current) => [...current, ...fresh.map(({ key }) => ({ key, preview: "", status: "uploading" as const }))]);
    for (const { key, file } of fresh) await sendOne(key, file); // one by one: kind to a slow mobile network
  }

  function move(index: number, by: -1 | 1) {
    setPhotos((list) => {
      const next = [...list];
      const target = index + by;
      if (target < 0 || target >= next.length) return list;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  const uploading = photos.some((p) => p.status === "uploading");
  const failed = photos.some((p) => p.status === "error");
  const canSend = title.trim().length > 0 && !uploading;

  async function send() {
    setSending(true);
    setError("");
    try {
      await submitNews({ title, body, photos: photos.filter((p) => p.path).map((p) => p.path as string), category_id: category });
      onSent();
    } catch (err) {
      setError(err instanceof AppError ? err.message : "Yuborib bo'lmadi.");
    } finally {
      setSending(false);
    }
  }

  function back() {
    if (!dirty || window.confirm("Yozilgan narsa o'chib ketadi. Chiqasizmi?")) onBack();
  }

  return (
    <Screen>
      <div className="flex items-center gap-2">
        <button type="button" onClick={back} className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-full bg-[var(--card)] text-xl text-[color:var(--fg)]" aria-label="Orqaga">
          <i className="ri-arrow-left-s-line" aria-hidden="true" />
        </button>
        <h1 className="text-xl font-bold text-[color:var(--fg)]">Yangi yangilik</h1>
      </div>

      <section className={card}>
        <div className="mb-2 flex items-baseline justify-between">
          <h2 className="text-sm font-semibold text-[color:var(--fg)]">Rasmlar</h2>
          <span className="text-xs text-[color:var(--hint)]">{photos.length} / {me.limits.photos}</span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {photos.map((photo, index) => (
            <div key={photo.key} className="relative aspect-square overflow-hidden rounded-xl bg-[var(--bg)]">
              {photo.preview && <img src={photo.preview} alt="" className="h-full w-full object-cover" />}
              {photo.status === "uploading" && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/35 text-white"><i className="ri-loader-4-line animate-spin text-2xl" aria-hidden="true" /></div>
              )}
              {photo.status === "error" && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 bg-red-700/80 p-1 text-center text-[10px] leading-tight text-white">
                  <i className="ri-error-warning-line text-lg" aria-hidden="true" />
                  {photo.error}
                </div>
              )}
              {index === 0 && photo.status !== "error" && <span className="absolute left-1 top-1 rounded-md bg-black/60 px-1.5 py-0.5 text-[10px] font-semibold text-white">Muqova</span>}
              <button type="button" onClick={() => setPhotos((list) => list.filter((p) => p.key !== photo.key))} className="absolute right-1 top-1 flex h-7 w-7 cursor-pointer items-center justify-center rounded-full bg-black/60 text-white" aria-label="Rasmni olib tashlash">
                <i className="ri-close-line" aria-hidden="true" />
              </button>
              {photos.length > 1 && (
                <div className="absolute inset-x-1 bottom-1 flex justify-between">
                  <button type="button" disabled={index === 0} onClick={() => move(index, -1)} className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-full bg-black/60 text-white disabled:opacity-30" aria-label="Oldinga">
                    <i className="ri-arrow-left-s-line" aria-hidden="true" />
                  </button>
                  <button type="button" disabled={index === photos.length - 1} onClick={() => move(index, 1)} className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-full bg-black/60 text-white disabled:opacity-30" aria-label="Orqaga surish">
                    <i className="ri-arrow-right-s-line" aria-hidden="true" />
                  </button>
                </div>
              )}
            </div>
          ))}
          {photos.length < me.limits.photos && (
            <button type="button" onClick={() => fileInput.current?.click()} className="flex aspect-square cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-[var(--line)] text-[color:var(--hint)]">
              <i className="ri-image-add-line text-3xl" aria-hidden="true" />
              <span className="text-xs font-medium">Rasm qo'shish</span>
            </button>
          )}
        </div>
        <input ref={fileInput} type="file" accept="image/*" multiple className="hidden" onChange={(e) => void addFiles(e.target.files)} />
        <p className="mt-2 text-xs text-[color:var(--hint)]">Birinchi rasm yangilikning muqovasi bo'ladi. Tartibini strelkalar bilan o'zgartirasiz.</p>
        {failed && <p className="mt-2 text-xs font-medium text-red-600">Ba'zi rasmlar yuklanmadi: ularni olib tashlab, qayta qo'shing.</p>}
      </section>

      <section className={`${card} space-y-4`}>
        <Field label="Sarlavha" hint={`${title.length}/${me.limits.title}`}>
          <input className={input} value={title} maxLength={me.limits.title} onChange={(e) => setTitle(e.target.value)} placeholder="Yangilik nima haqida?" />
        </Field>
        <Field label="Matn" hint={`${body.length}/${me.limits.text}`}>
          <textarea className={`${input} min-h-40 resize-y`} value={body} maxLength={me.limits.text} onChange={(e) => setBody(e.target.value)} placeholder="Nima bo'ldi, qachon, kim ishtirok etdi..." />
        </Field>
        {me.categories.length > 1 && (
          <div>
            <span className="mb-1.5 block text-sm font-semibold text-[color:var(--fg)]">Bo'lim</span>
            <div className="flex flex-wrap gap-2">
              {me.categories.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setCategory(c.id)}
                  aria-pressed={category === c.id}
                  className={`cursor-pointer rounded-full px-3.5 py-1.5 text-sm font-medium ${category === c.id ? "bg-[var(--accent)] text-[color:var(--accent-fg)]" : "border border-[var(--line)] text-[color:var(--fg)]"}`}
                >
                  {c.title}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>

      {error && <Notice tone="error">{error}</Notice>}
      <Notice tone="info">Yuborganingizdan keyin yangilikni admin ko'rib chiqadi. Tasdiqlansa, saytda chiqadi.</Notice>

      <div className="fixed inset-x-0 bottom-0 border-t border-[var(--line)] bg-[var(--card)] px-4 py-3">
        <div className="mx-auto max-w-md">
          <button type="button" onClick={send} disabled={!canSend || sending} className={primary}>
            {sending ? <><i className="ri-loader-4-line animate-spin" aria-hidden="true" /> Yuborilmoqda...</> : uploading ? "Rasmlar yuklanmoqda..." : <><i className="ri-send-plane-fill" aria-hidden="true" /> Yuborish</>}
          </button>
          {!title.trim() && <p className="mt-1.5 text-center text-xs text-[color:var(--hint)]">Yuborish uchun sarlavha yozing.</p>}
        </div>
      </div>
    </Screen>
  );
}

function Done({ onMore }: { onMore: () => void }) {
  return (
    <Screen>
      <div className={`${card} space-y-3 py-10 text-center`}>
        <i className="ri-checkbox-circle-fill text-6xl text-green-600" aria-hidden="true" />
        <h1 className="text-2xl font-bold text-[color:var(--fg)]">Yuborildi!</h1>
        <p className="text-sm text-[color:var(--hint)]">Admin yangilikni ko'rib chiqadi. Tasdiqlansa, saytda chiqadi. Holatini «Mening yangiliklarim»da ko'rasiz.</p>
      </div>
      <button type="button" onClick={onMore} className={primary}>Bosh sahifaga qaytish</button>
      <button type="button" onClick={close} className={ghost}>Yopish</button>
    </Screen>
  );
}

// --- the app ---------------------------------------------------------------------------------------------------

export default function TelegramApp() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState("");
  const [view, setView] = useState<"home" | "compose" | "done">("home");

  useEffect(() => {
    document.title = "FJSTI — yangilik yuborish";
    document.body.style.background = theme.secondary_bg_color || theme.bg_color || FALLBACK.bg;
    ready();
    expand();
  }, []);

  const load = useCallback(() => {
    setError("");
    getMe()
      .then(setMe)
      .catch((err) => setError(err instanceof AppError ? err.message : "Ilovani yuklab bo'lmadi."));
  }, []);

  useEffect(() => {
    if (initData) load();
  }, [load]);

  let content: ReactNode;
  if (!initData) {
    content = (
      <Screen>
        <div className={`${card} space-y-2 text-center`}>
          <i className="ri-telegram-line text-5xl text-[color:var(--hint)]" aria-hidden="true" />
          <h1 className="text-lg font-bold text-[color:var(--fg)]">Telegram ichidan oching</h1>
          <p className="text-sm text-[color:var(--hint)]">Bu sahifa faqat Telegram botidagi «Yangilik yuborish» tugmasi orqali ochiladi.</p>
        </div>
      </Screen>
    );
  } else if (error) {
    content = (
      <Screen>
        <Notice tone="error">{error}</Notice>
        <button type="button" onClick={load} className={ghost}><i className="ri-refresh-line" aria-hidden="true" /> Qayta urinish</button>
      </Screen>
    );
  } else if (!me) {
    content = <Screen><p className="pt-20 text-center text-sm text-[color:var(--hint)]">Yuklanmoqda...</p></Screen>;
  } else if (!me.registered) {
    content = <Register me={me} onDone={setMe} />;
  } else if (me.status !== "active") {
    content = <Waiting me={me} onRefresh={load} />;
  } else if (view === "compose") {
    content = (
      <Compose
        me={me}
        onBack={() => setView("home")}
        onSent={() => {
          setView("done");
          load();
        }}
      />
    );
  } else if (view === "done") {
    content = <Done onMore={() => setView("home")} />;
  } else {
    content = <Home me={me} onNew={() => setView("compose")} />;
  }

  return (
    <div style={{ ...palette, background: "var(--bg)", minHeight: "100vh" }} className="font-body">
      {content}
    </div>
  );
}
