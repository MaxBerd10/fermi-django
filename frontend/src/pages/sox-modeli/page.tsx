import PageHeader from "@/components/shared/PageHeader";
import DocumentCard from "@/blocks/DocumentCard";
import { usePageMeta } from "@/hooks/usePageMeta";

/*
 * "So‘x modeli" — the institute's 2026 report on the So‘x district: a short introduction and the report itself as the
 * site's usual file card (open in the browser / download). Uzbek only: the report is Uzbek. The figures below are the
 * report's own.
 */

const PDF_URL = "/files/Sox-modeli-hisobot-2026.pdf";
const PDF_BYTES = 2275197;

const RESULTS = [
  "So‘x tumanining 85 129 nafar aholisi yagona raqamli registrga kiritildi.",
  "39 025 nafar aholi qayta klinik ko‘rikdan o‘tdi; tibbiy yozuvlarning 34,4 foizi klinik holatga mos kelmagani aniqlanib, tuzatildi.",
  "Dispanser nazoratiga olinganlar soni 11 890 nafardan 33 360 nafarga yetdi.",
  "14 ta mobil brigada tuman bo‘yicha barcha mahallalarda ish olib bordi; 400 dan ortiq shifokor tibbiy ko‘riklarda qatnashdi.",
  "14 nafar shifokor va 13 nafar IT-hamshira AI Shifokor va iShifo bo‘yicha o‘qitildi; institut shifokorlari bilan 23 ta onlayn konsultatsiya o‘tkazildi.",
];

export default function SoxModeliPage() {
  usePageMeta(
    "So‘x modeli",
    "Farg‘ona jamoat salomatligi tibbiyot instituti hisoboti (2026): So‘x tumani sog‘liqni saqlash tizimi, verifikatsiya natijalari, AI Shifokor va iShifo platformalari, takliflar.",
  );

  return (
    <div className="text-foreground-950">
      <PageHeader title="So‘x modeli" compact />

      <div className="section-container section-pad !pt-3">
        <div className="page-card mx-auto max-w-4xl p-5 md:p-8">
          <div className="space-y-4 text-base leading-relaxed text-[#333]">
            <p>
              <strong>So‘x modeli</strong> — Farg‘ona jamoat salomatligi tibbiyot instituti tomonidan So‘x tumanida sun’iy intellekt, teletibbiyot va raqamli boshqaruv asosida joriy etilgan tibbiy xizmatning yangi modeli.
            </p>
            <p>
              Hisobot O‘zbekiston Respublikasi Prezidentining 2022-yil 28-yanvardagi PQ–60-sonli qaroriga muvofiq, Sog‘liqni saqlash vazirligi va Prezident administratsiyasi topshirig‘i asosida tayyorlangan. Unda tuman sog‘liqni saqlash tizimining real holati, ma’lumotlarni verifikatsiya qilish natijalari, AI Shifokor va iShifo platformalari, kadrlar tanqisligi, laboratoriya, moliyalashtirish bo‘yicha takliflar bayon etilgan.
            </p>
            <div>
              <p className="font-semibold text-[#0a1158]">Asosiy natijalar</p>
              <ul className="mt-2 list-disc space-y-1.5 pl-5">
                {RESULTS.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            </div>
            <p>To‘liq hisobotni quyidagi fayl orqali brauzerda ochib o‘qish yoki yuklab olish mumkin.</p>
          </div>

          <DocumentCard url={PDF_URL} title="So‘x modeli — hisobot, 2026" filename="Sox-modeli-hisobot-2026.pdf" fileSize={PDF_BYTES} />
        </div>
      </div>
    </div>
  );
}
