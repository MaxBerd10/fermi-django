import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Reveal } from "@/components/Animation";
import { useHomeSections } from "@/api/homeSections";

const VOICE_IDS = ["v1", "v2", "v3", "v4"] as const;
const FACT_IDS = ["fact1", "fact2", "fact3", "fact4"] as const;

const initialsOf = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join("");

export default function StudentVoices() {
  const { t } = useTranslation();
  const sections = useHomeSections();
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);

  // the editable lists; the built-in ones only if the request failed
  const voices = sections
    ? sections.voices.map((v) => ({ id: String(v.id), quote: v.quote, name: v.name, meta: v.meta }))
    : VOICE_IDS.map((id) => ({
        id,
        quote: t(`voices.${id}.quote`),
        name: t(`voices.${id}.name`),
        meta: t(`voices.${id}.meta`),
      }));
  const facts = sections
    ? sections.facts.map((f) => ({ id: String(f.id), value: f.value, label: f.label }))
    : FACT_IDS.map((id) => ({ id, value: t(`voices.${id}.value`), label: t(`voices.${id}.label`) }));
  const count = voices.length;

  useEffect(() => {
    if (paused || count < 2) return;
    const id = window.setInterval(() => {
      setIndex((i) => (i + 1) % count);
    }, 6500);
    return () => window.clearInterval(id);
  }, [paused, count]);

  if (sections === undefined) return <div className="min-h-[441px] lg:min-h-[301px]" aria-hidden="true" />;
  if (voices.length === 0 && facts.length === 0) return null;
  const voice = voices[index % Math.max(count, 1)];

  return (
    <section className="py-5 md:py-6 bg-transparent overflow-hidden relative border-t border-[#e5e5e5]/60">
      <div className="section-container relative z-10">
        <Reveal className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2 mb-4">
          <div className="max-w-xl">
            <p className="section-eyebrow !mb-1.5">{t("voices.eyebrow")}</p>
            <h2 className="font-heading text-xl md:text-2xl font-bold text-[#0a0a0a] tracking-tight">
              {t("voices.headingPrefix")} {t("voices.headingHighlight")}
            </h2>
          </div>
        </Reveal>

        <div className="grid lg:grid-cols-12 gap-4 lg:gap-6 items-start">
          {voice && (
            <Reveal className="lg:col-span-7">
              <div
                className="rounded-2xl border border-[#e5e5e5]/80 bg-white/95 p-4 md:p-5"
                onMouseEnter={() => setPaused(true)}
                onMouseLeave={() => setPaused(false)}
              >
                {/* Every quote sits in the same grid cell, only the current one visible: the card is as tall as the
                    longest quote, so the sections below never jump when the quotes change (editors may write any length). */}
                <div className="grid">
                  {voices.map((v, i) => (
                    <div
                      key={v.id}
                      aria-hidden={i !== index % count}
                      className={`[grid-area:1/1] transition-opacity duration-300 ${i === index % count ? "opacity-100" : "invisible opacity-0"}`}
                    >
                      <p className="font-heading text-lg md:text-xl text-[#0a0a0a] font-medium leading-snug line-clamp-6">
                        “{v.quote}”
                      </p>
                      <div className="mt-3 flex items-center gap-2.5">
                        <span className="w-8 h-8 rounded-lg border border-[#e5e5e5] bg-white flex items-center justify-center text-xs font-bold text-[#0a1158]">
                          {initialsOf(v.name)}
                        </span>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-[#0a0a0a] truncate">{v.name}</p>
                          <p className="text-[11px] font-semibold text-[#0a1158] uppercase tracking-wide truncate">{v.meta}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex gap-1.5">
                  {voices.map((v, i) => (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => setIndex(i)}
                      className={`h-1 rounded-full transition-all cursor-pointer ${
                        i === index % count ? "w-6 bg-[#0a1158]" : "w-2 bg-[#e5e5e5] hover:bg-[#ffd600]"
                      }`}
                      aria-label={t("voices.dot", { n: i + 1 })}
                    />
                  ))}
                </div>
              </div>
            </Reveal>
          )}

          {facts.length > 0 && (
            <Reveal delay={40} className="lg:col-span-5">
              <div className="grid grid-cols-2 gap-2">
                {facts.map((fact) => (
                  <div key={fact.id} className="rounded-xl border border-[#e5e5e5]/80 bg-white/95 px-3 py-2.5">
                    <p className="font-heading text-xl font-bold text-[#0a1158] tabular-nums leading-none">{fact.value}</p>
                    <p className="mt-1 text-[11px] text-[#333333] leading-snug">{fact.label}</p>
                  </div>
                ))}
              </div>
            </Reveal>
          )}
        </div>
      </div>
    </section>
  );
}
