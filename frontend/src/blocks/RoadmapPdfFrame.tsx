import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import DocumentCard from "./DocumentCard";

// The browser's own PDF viewer builds its toolbar after the frame has loaded, which pushes the page it shows
// down by the toolbar's height. That happens inside the frame, but Lighthouse adds it to the page's layout shift
// (0.17 on a page that is nothing but a PDF). The frame is therefore kept invisible, with a placeholder of the
// same size, until the viewer has had time to finish its own layout.
const VIEWER_SETTLE_MS = 1500;
// if the frame's load event never comes (blocked, offline), show whatever is there rather than a blank box
const GIVE_UP_MS = 10000;

// Phones and tablets cannot show a PDF inside a frame (iOS shows the first page only, Android Chrome a blank box with
// a download prompt), so there the card with its two buttons (open, download) is all the visitor gets.
const NO_INLINE_PDF = "(max-width: 767px), (pointer: coarse)";

function useCannotShowPdfInline(): boolean {
  const [cannot, setCannot] = useState(() => typeof window !== "undefined" && window.matchMedia(NO_INLINE_PDF).matches);
  useEffect(() => {
    const query = window.matchMedia(NO_INLINE_PDF);
    const update = () => setCannot(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return cannot;
}

function PdfViewer({ src, title }: { src: string; title: string }) {
  const { t } = useTranslation();
  const cannotShowInline = useCannotShowPdfInline();
  const [ready, setReady] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    if (cannotShowInline) return;
    const url = new URL(src, window.location.href);
    if (url.origin !== window.location.origin) {
      setAvailable(true);
      return;
    }
    const controller = new AbortController();
    fetch(url, { method: "HEAD", signal: controller.signal })
      .then((response) => {
        if (!controller.signal.aborted) {
          setAvailable(response.ok && /^application\/pdf\b/i.test(response.headers.get("content-type") ?? ""));
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setAvailable(false);
      });
    return () => controller.abort();
  }, [src, cannotShowInline]);

  useEffect(() => {
    if (!available) return;
    const giveUp = window.setTimeout(() => setReady(true), GIVE_UP_MS);
    timers.current.push(giveUp);
    const pending = timers.current;
    return () => pending.forEach((timer) => window.clearTimeout(timer));
  }, [available]);

  if (cannotShowInline || available !== true) return null;

  return (
    <div className="cms-roadmap-pdf__frame">
      {!ready && (
        <div className="cms-roadmap-pdf__loading" role="status">
          <i className="ri-loader-4-line animate-spin" aria-hidden="true" />
          {t("test.loading")}
        </div>
      )}
      <iframe
        src={src}
        title={title}
        className="cms-roadmap-pdf__iframe"
        style={ready ? undefined : { visibility: "hidden" }}
        onLoad={() => timers.current.push(window.setTimeout(() => setReady(true), VIEWER_SETTLE_MS))}
      />
    </div>
  );
}

export default function RoadmapPdfFrame({
  src, title, filename, fileSize,
}: { src: string; title: string; filename: string; fileSize: number }) {
  return (
    <section className="space-y-4" aria-label={title}>
      {/* the buttons (open in the browser, download) come first: the viewer below can be very long */}
      <DocumentCard url={src} title={title} filename={filename} fileSize={fileSize} />
      <PdfViewer key={src} src={src} title={title} />
    </section>
  );
}
