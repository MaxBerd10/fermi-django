import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

// The browser's own PDF viewer builds its toolbar after the frame has loaded, which pushes the page it shows
// down by the toolbar's height. That happens inside the frame, but Lighthouse adds it to the page's layout shift
// (0.17 on a page that is nothing but a PDF). The frame is therefore kept invisible, with a placeholder of the
// same size, until the viewer has had time to finish its own layout.
const VIEWER_SETTLE_MS = 1500;
// if the frame's load event never comes (blocked, offline), show whatever is there rather than a blank box
const GIVE_UP_MS = 10000;

export default function RoadmapPdfFrame({ src, title }: { src: string; title: string }) {
  const { t } = useTranslation();
  const [ready, setReady] = useState(false);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    const giveUp = window.setTimeout(() => setReady(true), GIVE_UP_MS);
    timers.current.push(giveUp);
    const pending = timers.current;
    return () => pending.forEach((timer) => window.clearTimeout(timer));
  }, []);

  return (
    <div className="cms-roadmap-pdf__frame cms-roadmap-pdf__frame--viewer">
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
