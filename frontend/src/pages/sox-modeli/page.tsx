import PageHeader from "@/components/shared/PageHeader";
import DocumentCard from "@/blocks/DocumentCard";
import { usePageMeta } from "@/hooks/usePageMeta";

/*
 * "Soʻx modeli" — the institute's 2026 report on the Soʻx district: a short introduction and the report itself as the
 * site's usual file card (open in the browser / download). Uzbek only: the report is Uzbek. The figures below are the
 * report's own.
 */

const PDF_URL = "/files/Sox-modeli-hisobot-2026.pdf";
const PDF_BYTES = 2275197;

const RESULTS = [
  "Soʻx tumanining 85 129 nafar aholisi yagona raqamli registrga kiritildi.",
  "39 025 nafar aholi qayta klinik koʻrikdan oʻtdi; tibbiy yozuvlarning 34,4 foizi klinik holatga mos kelmagani aniqlanib, tuzatildi.",
  "Dispanser nazoratiga olinganlar soni 11 890 nafardan 33 360 nafarga yetdi.",
  "14 ta mobil brigada tuman boʻyicha barcha mahallalarda ish olib bordi; 400 dan ortiq shifokor tibbiy koʻriklarda qatnashdi.",
  "14 nafar shifokor va 13 nafar IT-hamshira AI Shifokor va iShifo boʻyicha oʻqitildi; institut shifokorlari bilan 23 ta onlayn konsultatsiya oʻtkazildi.",
];

export default function SoxModeliPage() {
  usePageMeta(
    "Soʻx modeli",
    "Fargʻona jamoat salomatligi tibbiyot instituti hisoboti (2026): Soʻx tumani sogʻliqni saqlash tizimi, verifikatsiya natijalari, AI Shifokor va iShifo platformalari, takliflar.",
  );

  return (
    <div className="text-foreground-950">
      <PageHeader title="Soʻx modeli" compact />

      <div className="section-container section-pad !pt-2 md:!pt-3">
        <div className="page-card p-5 md:p-6">
          <img
            src="/images/sox/sox-modeli-banner.webp"
            alt="Shifokor va keksa bemor, Soʻx tumani manzarasi"
            width={1411}
            height={430}
            className="h-48 w-full rounded-xl object-cover object-bottom sm:h-64 lg:h-80"
          />
          <div className="mt-6 space-y-4 text-base leading-relaxed text-[#333]">
            <p>
              <strong>Soʻx modeli</strong> — Fargʻona jamoat salomatligi tibbiyot instituti tomonidan Soʻx tumanida sunʻiy intellekt, teletibbiyot va raqamli boshqaruv asosida joriy etilgan tibbiy xizmatning yangi modeli.
            </p>
            <p>
              Hisobot Oʻzbekiston Respublikasi Prezidentining 2022-yil 28-yanvardagi PQ–60-sonli qaroriga muvofiq, Sogʻliqni saqlash vazirligi va Prezident administratsiyasi topshirigʻi asosida tayyorlangan. Unda tuman sogʻliqni saqlash tizimining real holati, maʻlumotlarni verifikatsiya qilish natijalari, AI Shifokor va iShifo platformalari, kadrlar tanqisligi, laboratoriya, moliyalashtirish boʻyicha takliflar bayon etilgan.
            </p>
            <div>
              <p className="font-semibold text-[#0a1158]">Asosiy natijalar</p>
              <ul className="mt-2 list-disc space-y-1.5 pl-5">
                {RESULTS.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
            </div>
            <p>Toʻliq hisobotni quyidagi fayl orqali brauzerda ochib oʻqish yoki yuklab olish mumkin.</p>
          </div>

          <DocumentCard url={PDF_URL} title="Soʻx modeli — hisobot, 2026" filename="Sox-modeli-hisobot-2026.pdf" fileSize={PDF_BYTES} />
        </div>
      </div>
    </div>
  );
}
