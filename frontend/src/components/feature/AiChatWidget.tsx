import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { aiChat, staticAiReply, type AiSource } from "@/api/ai";
import { goAiHref, renderAiText } from "@/components/ai/renderAiText";
import { FEATURES } from "@/lib/featureFlags";
import { getSettings } from "@/api/settings";

type Msg = { role: "user" | "assistant"; content: string; sources?: AiSource[] };

const QUICK = ["ai.quick1", "ai.quick2", "ai.quick3", "ai.quick4"] as const;

// Address/phone/contact questions are the single most common thing asked here (see
// ai.quick4) and the answer never needs an LLM -- it's the same handful of facts
// Footer.tsx already shows, sourced from the real (admin-editable) settings API. Answer
// these directly, with no dependency on FEATURES.ai/an OpenAI key, so this keeps working
// even while the AI backend itself is unconfigured.
const CONTACT_KEYWORDS = [
  "manzil", "joylash", "qayerda", "qayerd", "telefon", "raqam", "bog'lan", "boglan",
  "aloqa", "pochta", "email", "e-mail",
  "адрес", "где наход", "телефон", "номер", "связ", "контакт", "почта",
  "address", "located", "location", "phone", "number", "contact", "reach you", "e-mail",
];

function isContactQuery(q: string): boolean {
  const lower = q.toLowerCase();
  return CONTACT_KEYWORDS.some((k) => lower.includes(k));
}

export default function AiChatWidget() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: t("ai.welcome") },
  ]);
  const [contact, setContact] = useState<{ address: string; phone: string; email: string } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getSettings().then((s) => {
      setContact({
        address: s.setting?.address?.trim() || "Farg'ona sh., Yangi Turon, 2-a uy",
        phone: s.setting?.phone?.trim() || "+998 95 062-23-45, +998 95 063-23-45",
        email: s.setting?.email?.trim() || "info@fjsti.uz, fmioz@mail.ru",
      });
    });
  }, []);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open, loading]);

  useEffect(() => {
    setMessages([{ role: "assistant", content: t("ai.welcome") }]);
  }, [i18n.language, t]);

  useEffect(() => {
    const close = () => setOpen(false);
    window.addEventListener("fjsti-ai-close", close);
    return () => window.removeEventListener("fjsti-ai-close", close);
  }, []);

  async function send(text: string) {
    const q = text.trim();
    if (!q || loading) return;
    setError("");
    const next: Msg[] = [...messages, { role: "user", content: q }];
    setMessages(next);
    setInput("");

    if (contact && isContactQuery(q)) {
      const reply = t("ai.contactAnswer", contact);
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
      return;
    }

    // Common institute facts are free, local answers. Do this before checking
    // the paid model flag, so HEMIS/admissions/faculties remain useful whenever
    // OpenAI is deliberately disabled.
    const staticReply = staticAiReply(q, i18n.language);
    if (staticReply) {
      setMessages((m) => [...m, { role: "assistant", content: staticReply.reply, sources: staticReply.sources }]);
      return;
    }

    if (!FEATURES.ai) {
      setMessages((m) => [...m, { role: "assistant", content: t("ai.staticOnly") }]);
      return;
    }
    setLoading(true);
    try {
      const res = await aiChat(
        next.map((m) => ({ role: m.role, content: m.content })),
        i18n.language,
      );
      setMessages((m) => [...m, { role: "assistant", content: res.reply, sources: res.sources }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ai.error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="fixed right-4 bottom-4 z-50 flex items-center gap-2 h-12 pl-3 pr-4 rounded-full bg-[#0a1158] text-white shadow-[0_12px_32px_rgba(10,17,88,0.35)] hover:bg-[#060a3d] transition-colors cursor-pointer"
        aria-label={t("ai.open")}
      >
        <span className="w-8 h-8 rounded-full bg-[#ffd600] text-[#0a1158] inline-flex items-center justify-center">
          <i className="ri-robot-2-line text-lg" />
        </span>
        <span className="text-sm font-semibold hidden sm:inline">{t("ai.fab")}</span>
      </button>

      {open && (
        <div className="fixed right-4 bottom-20 z-50 w-[calc(100vw-2rem)] max-w-[380px] h-[70vh] max-h-[520px] flex flex-col rounded-2xl border border-[#e5e5e5] bg-white shadow-2xl overflow-hidden">
          <div className="flex items-center justify-between gap-2 px-4 py-3 bg-[#0a1158] text-white">
            <div className="min-w-0">
              <p className="font-heading font-semibold text-sm">{t("ai.title")}</p>
              <p className="text-[11px] text-white/70 truncate">{t("ai.subtitle")}</p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="w-8 h-8 rounded-lg hover:bg-white/10 cursor-pointer"
              aria-label="Close"
            >
              <i className="ri-close-line text-xl" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 bg-[#f7f8fc]">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`max-w-[90%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "ml-auto bg-[#0a1158] text-white"
                    : "mr-auto bg-white border border-[#e5e5e5] text-[#0a0a0a]"
                }`}
              >
                <div className="whitespace-pre-wrap">
                  {m.role === "assistant" ? renderAiText(m.content, false) : m.content}
                </div>
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.sources.slice(0, 3).map((s) => (
                      <button
                        key={s.href + s.title}
                        type="button"
                        onClick={() => goAiHref(s.href, navigate)}
                        className="text-[10px] px-2 py-0.5 rounded-full bg-[#0a1158]/8 text-[#0a1158] font-medium cursor-pointer hover:bg-[#0a1158]/15"
                      >
                        {s.title}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <p className="text-xs text-[#555555] px-1">
                <i className="ri-loader-4-line animate-spin inline-block mr-1" />
                {t("ai.thinking")}
              </p>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="px-3 pt-2 flex flex-wrap gap-1.5 border-t border-[#e5e5e5] bg-white">
            {QUICK.map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => send(t(k))}
                className="text-[11px] px-2.5 py-1 rounded-full border border-[#e5e5e5] hover:border-[#ffd600] text-[#0a1158] cursor-pointer"
              >
                {t(k)}
              </button>
            ))}
          </div>

          {error && <p className="px-3 text-xs text-red-600">{error}</p>}

          <form
            className="p-3 flex gap-2 bg-white"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t("ai.placeholder")}
              className="flex-1 h-10 px-3 rounded-xl border border-[#e5e5e5] text-sm focus:outline-none focus:border-[#0a1158]"
            />
            <button
              type="submit"
              disabled={loading}
              className="h-10 w-10 rounded-xl bg-[#ffd600] text-[#0a1158] inline-flex items-center justify-center cursor-pointer disabled:opacity-50"
            >
              <i className="ri-send-plane-2-fill" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
