import { useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import DOMPurify from "dompurify";
import { enhanceCmsHtml } from "@/lib/enhanceCmsHtml";
import { optimizedImageUrl } from "@/lib/imageProxy";
import { MenuSectionOriginContext, inAppPath } from "@/lib/menuSectionOrigin";
import { findMenuTitleBySlug } from "@/lib/menuSection";
import { normalizeYearLabels } from "@/lib/siteConstants";
import { useMenu } from "@/context/MenuContext";
// Moved here from main.tsx (see that file's remaining imports) -- these style
// enhanceCmsHtml's output, which only this component ever calls, so loading
// them eagerly on every route (including ones that never render CMS HTML,
// like the homepage) was pure render-blocking dead weight there.
import "@/styles/cms-content.css";
import "@/styles/buildings-content.css";
import "@/styles/conference-content.css";
import "@/styles/newspaper-content.css";
import "@/styles/regulatory-content.css";

// This renders CKEditor output from CMS admins, but ALSO `article.content` for
// Telegram-scraped posts (see DetailPage) — HTML pulled from a public channel's
// page, not admin-authored. Sanitize unconditionally so a compromised/malicious
// channel post can't run script via onerror=/onload=/javascript: hrefs etc.
// iframe is allowed (CMS content embeds YouTube/Google Maps/Docs viewers) but its
// src is restricted to those known-safe hosts via the hook below.
const IFRAME_HOST_ALLOWLIST = [
  "www.youtube.com",
  "youtube.com",
  "www.google.com",
  "docs.google.com",
];

DOMPurify.addHook("uponSanitizeElement", (node, data) => {
  if (data.tagName !== "iframe") return;
  const el = node as unknown as HTMLIFrameElement;
  const src = el.getAttribute?.("src") || "";
  let allowed = false;
  try {
    allowed = IFRAME_HOST_ALLOWLIST.includes(new URL(src, window.location.origin).hostname);
  } catch {
    allowed = false;
  }
  if (!allowed) el.remove();
});

// Content-embedded photos (CKEditor inserts, gallery grids inside an article body...)
// are the same unresized CMS originals as everywhere else — route them through the
// same resize/compress cache. A generous fixed width covers both a full-width single
// image and a multi-column grid reasonably well without a per-image size hint (which
// raw HTML from the CMS doesn't carry).
DOMPurify.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName !== "IMG") return;
  const el = node as unknown as HTMLImageElement;
  const src = el.getAttribute?.("src");
  if (src) el.setAttribute("src", optimizedImageUrl(src, 1200));
});

function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ["iframe"],
    ADD_ATTR: ["allow", "allowfullscreen", "frameborder", "target"],
  });
}

export default function RichContent({
  html,
  className = "",
  enhanced = true,
  slug,
}: {
  html: string;
  className?: string;
  enhanced?: boolean;
  slug?: string;
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const originSection = useContext(MenuSectionOriginContext);
  const usmleTitle = t("usmle.introTitle");
  const { menu } = useMenu();
  const processed = useMemo(() => {
    const pageTitle = (target: string) => {
      const title = findMenuTitleBySlug(menu, target);
      return title && normalizeYearLabels(title);
    };
    const withLayout = enhanced ? enhanceCmsHtml(html, { slug, usmleTitle, pageTitle }) : html;
    return sanitizeHtml(withLayout);
  }, [html, enhanced, slug, usmleTitle, menu]);

  if (!processed) return null;

  // A link to another page of the site opens inside the app (no reload) and tells that page which section it
  // was clicked in. Files, outside sites, new-tab and modifier clicks stay with the browser.
  const onClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const anchor = (event.target as Element).closest("a[href]");
    if (!anchor || anchor.hasAttribute("download") || (anchor.getAttribute("target") || "_self") !== "_self") return;
    const path = inAppPath(anchor.getAttribute("href") || "", window.location.origin);
    if (!path) return;
    event.preventDefault();
    navigate(path, { state: originSection ? { menuSection: originSection } : undefined });
  };

  return (
    <div
      className={`prose-content [&_img]:!max-w-full [&_img]:!h-auto [&_img]:!w-auto [&_iframe]:!w-full [&_iframe]:!h-auto [&_iframe]:aspect-video ${className}`}
      onClick={onClick}
      dangerouslySetInnerHTML={{ __html: processed }}
    />
  );
}
