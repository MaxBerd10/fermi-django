import type { LocalizedImage } from "../types";

const API_BASE = "http://127.0.0.1:8000";

/**
 * Renders from the backend's real, Pillow-measured width/height — never a
 * guessed "logo vs photo" classification from an arbitrary insertion width.
 * Setting the CSS aspect-ratio from real data reserves the right box before
 * the image loads (no layout jump) and keeps every image's true proportions,
 * whatever size the page displays it at.
 */
export function ResponsiveImage({
  image,
  className = "",
  maxWidthClass = "max-w-xs",
}: {
  image: LocalizedImage;
  className?: string;
  maxWidthClass?: string;
}) {
  const src = image.file.startsWith("http") ? image.file : `${API_BASE}${image.file}`;
  return (
    <img
      src={src}
      alt={image.alt_text}
      width={image.width ?? undefined}
      height={image.height ?? undefined}
      style={image.width && image.height ? { aspectRatio: `${image.width} / ${image.height}` } : undefined}
      className={`w-full ${maxWidthClass} h-auto object-contain ${className}`}
      loading="lazy"
    />
  );
}
