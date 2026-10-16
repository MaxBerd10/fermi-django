import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiClient } from "@/api/client";
import { useConfirm } from "../../components/ConfirmDialog";
import PageHeader from "../../components/PageHeader";
import { useToast } from "../../components/Toast";
import { adminErrorMessage } from "../../hooks/useAdminList";

interface BotInfo {
  enabled: boolean;
  username: string | null;
  invite_code: string;
  invite_link: string | null;
  bot_link: string | null;
  webhook_url: string;
  pending: number;
  active: number;
  approvers: number;
}

const SETUP_STEPS = [
  "Telegramda @BotFather ga yozing: /newbot — botga nom bering. U sizga uzun «token» beradi (uni hech kimga yubormang).",
  "Serverda atrof-muhit faylga ikki qator qo'shing: TELEGRAM_BOT_TOKEN=<token> va TELEGRAM_WEBHOOK_SECRET=<tasodifiy uzun matn>. Aniq buyruqni dasturchi beradi.",
  "Serverda bir marta ishga tushiring: manage.py telegram_set_webhook — bot saytga ulanadi.",
  "Servisni qayta ishga tushiring. Shu sahifa yangilansa, bot havolasi shu yerda chiqadi.",
];

function CopyButton({ text, label }: { text: string; label: string }) {
  const toast = useToast();
  return (
    <button
      type="button"
      onClick={() => navigator.clipboard.writeText(text).then(() => toast.success("Nusxalandi."), () => toast.error("Nusxalab bo'lmadi: matnni qo'lda belgilang."))}
      className="flex h-10 shrink-0 cursor-pointer items-center gap-2 rounded-lg border border-background-300 bg-background-50 px-3 text-sm font-medium text-foreground-700 hover:bg-background-100"
    >
      <i className="ri-file-copy-line" aria-hidden="true" /> {label}
    </button>
  );
}

export default function TelegramBotPage() {
  const toast = useToast();
  const confirm = useConfirm();
  const [info, setInfo] = useState<BotInfo | null>(null);
  const [error, setError] = useState("");
  const [rotating, setRotating] = useState(false);

  const load = useCallback(() => {
    apiClient
      .get<BotInfo>("admin/telegram-bot", undefined, true)
      .then(({ data }) => setInfo(data))
      .catch((err) => setError(adminErrorMessage(err, "Ma'lumotni yuklab bo'lmadi.")));
  }, []);

  useEffect(load, [load]);

  async function rotate() {
    const ok = await confirm({
      title: "Kirish havolasi almashtirilsinmi?",
      message: "Eski havola darhol ishlamay qoladi. Botga allaqachon kirgan xodimlarga ta'sir qilmaydi. Yangi havolani qayta tarqatishingiz kerak bo'ladi.",
      confirmLabel: "Ha, almashtirish",
      danger: true,
    });
    if (!ok) return;
    setRotating(true);
    try {
      const { data } = await apiClient.post<BotInfo>("admin/telegram-bot", { action: "rotate_code" }, true);
      setInfo(data);
      toast.success("Yangi havola tayyor.");
    } catch (err) {
      toast.error(adminErrorMessage(err, "Almashtirib bo'lmadi."));
    } finally {
      setRotating(false);
    }
  }

  const announcement = info?.invite_link
    ? `Hurmatli hamkasblar! Institut saytiga yangilik, rasm va e'lonlarni endi Telegram orqali yuborishingiz mumkin. Botga quyidagi havola orqali kiring, ism va bo'limingizni yozing, so'ng rasm va matnni yuboring (birinchi qator — sarlavha). Yangilikni admin ko'rib chiqib tasdiqlagach saytda chiqadi.\n\n${info.invite_link}`
    : "";

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Telegram bot"
        subtitle="Xodimlar yangilikni (rasm va matn) Telegram orqali yuboradi. U admin panelda qoralama bo'lib tushadi — siz tasdiqlamaguncha saytda chiqmaydi."
      />

      {error && <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      {!info && !error && <p className="text-sm text-foreground-500">Yuklanmoqda...</p>}

      {info && !info.enabled && (
        <section className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-sm text-amber-900">
          <h2 className="mb-2 flex items-center gap-2 font-semibold"><i className="ri-error-warning-line text-lg" aria-hidden="true" /> Bot hali ulanmagan</h2>
          <ol className="list-decimal space-y-2 pl-5 leading-relaxed">
            {SETUP_STEPS.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {info?.enabled && (
        <div className="space-y-4">
          <section className="rounded-xl border border-background-200 bg-background-50 p-5">
            <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-foreground-500">Kirish havolasi</h2>
            {info.invite_link ? (
              <>
                <p className="mb-2 text-sm text-foreground-600">
                  Shu havolani institut guruhlariga tashlang. Havola orqali kirgan odam ism va bo'limini yozadi va darhol yangilik yubora oladi.
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <code className="min-w-0 flex-1 truncate rounded-lg bg-background-100 px-3 py-2.5 text-sm text-foreground-800">{info.invite_link}</code>
                  <CopyButton text={info.invite_link} label="Nusxalash" />
                  <button
                    type="button"
                    onClick={rotate}
                    disabled={rotating}
                    className="flex h-10 shrink-0 cursor-pointer items-center gap-2 rounded-lg border border-background-300 px-3 text-sm font-medium text-foreground-700 hover:bg-background-100 disabled:opacity-60"
                  >
                    <i className="ri-refresh-line" aria-hidden="true" /> Havolani almashtirish
                  </button>
                </div>
                <details className="mt-4 text-sm text-foreground-600">
                  <summary className="cursor-pointer font-medium text-foreground-700">Guruhga tashlash uchun tayyor xabar</summary>
                  <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-background-100 p-3 font-sans text-sm leading-relaxed text-foreground-800">{announcement}</pre>
                  <div className="mt-2"><CopyButton text={announcement} label="Xabarni nusxalash" /></div>
                </details>
              </>
            ) : (
              <p className="text-sm text-amber-800">Botning nomini Telegramdan olib bo'lmadi. Token to'g'ri ekanini tekshiring.</p>
            )}
          </section>

          <section className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "Faol xodimlar", value: info.active },
              { label: "Ruxsat kutayotganlar", value: info.pending, warn: info.pending > 0 },
              { label: "Tasdiqlovchilar", value: info.approvers, warn: info.approvers === 0 },
            ].map((tile) => (
              <div key={tile.label} className={`rounded-xl border p-4 ${tile.warn ? "border-amber-300 bg-amber-50" : "border-background-200 bg-background-50"}`}>
                <div className="font-heading text-2xl font-bold tabular-nums text-foreground-950">{tile.value}</div>
                <div className="text-xs text-foreground-500">{tile.label}</div>
              </div>
            ))}
          </section>

          {info.approvers === 0 && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
              <b>Hali tasdiqlovchi yo'q.</b> Botdan yangilik haqida xabar olish uchun avval o'zingiz yuqoridagi havola orqali botga kiring (ism va bo'limni yozing). So'ng{" "}
              <Link to="/admin/telegram-users" className="font-semibold underline">xodimlar ro'yxatida</Link> o'zingizni oching va «Tasdiqlovchi» belgisini qo'ying.
            </div>
          )}

          <section className="flex flex-wrap gap-2 text-sm">
            <Link to="/admin/telegram-users" className="flex h-10 items-center gap-2 rounded-lg border border-background-300 bg-background-50 px-4 font-medium text-foreground-700 hover:bg-background-100">
              <i className="ri-team-line" aria-hidden="true" /> Xodimlar ro'yxati
            </Link>
            <Link to="/admin/news?source=telegram" className="flex h-10 items-center gap-2 rounded-lg border border-background-300 bg-background-50 px-4 font-medium text-foreground-700 hover:bg-background-100">
              <i className="ri-newspaper-line" aria-hidden="true" /> Telegramdan kelgan yangiliklar
            </Link>
          </section>
        </div>
      )}
    </div>
  );
}
