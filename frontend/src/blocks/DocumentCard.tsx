import { useTranslation } from "react-i18next";

interface DocumentCardProps {
  url: string;
  title: string;
  filename: string;
  fileSize: number;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * A downloadable file shown as a card -- name, type and size, plus "open in the browser" and
 * "download" -- instead of one bare button. Deliberately no embedded viewer: a 9 MB PDF in an
 * <iframe> loads in full on page open (slow, hurts the Lighthouse score) and phones only show its
 * first page anyway. The buttons carry `cms-download-btn` so the article link styling skips them.
 */
export default function DocumentCard({ url, title, filename, fileSize }: DocumentCardProps) {
  const { t } = useTranslation();
  const extension = (filename.split(".").pop() || "file").toUpperCase();
  const meta = [extension, fileSize > 0 ? formatFileSize(fileSize) : ""].filter(Boolean).join(" · ");

  return (
    <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-primary-100 bg-primary-50/40 p-4 lg:flex-row lg:items-center lg:p-5">
      <div className="flex min-w-0 flex-1 items-center gap-4">
        <span
          className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-[#0a1158] text-xl text-[#ffd600]"
          aria-hidden="true"
        >
          <i className="ri-file-pdf-2-line" />
        </span>
        <span className="min-w-0">
          <span className="block font-heading text-base font-bold leading-snug text-primary-900">{title}</span>
          <span className="mt-0.5 block text-sm text-foreground-600">{meta}</span>
        </span>
      </div>
      <div className="flex flex-col gap-2.5 sm:flex-row">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="cms-download-btn inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-[#0a1158] px-5 text-sm font-semibold text-white shadow-md transition-colors hover:bg-[#060a3d]"
        >
          <i className="ri-external-link-line" aria-hidden="true" />
          {t("document.open")}
        </a>
        <a
          href={url}
          download
          className="cms-download-btn inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-primary-200 bg-white px-5 text-sm font-semibold text-primary-900 transition-colors hover:border-[#0a1158]"
        >
          <i className="ri-download-2-line" aria-hidden="true" />
          {t("document.download")}
        </a>
      </div>
    </div>
  );
}
