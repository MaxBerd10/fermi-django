export type SocialPlatform = "facebook" | "twitter" | "youtube" | "telegram" | "instagram";

/** Remix icons for each platform -- all present in the remixicon SUBSET font (public/vendor/remixicon). */
export const SOCIAL_PLATFORM_ICON: Record<SocialPlatform, string> = {
  facebook: "ri-facebook-fill",
  twitter: "ri-twitter-x-line",
  youtube: "ri-youtube-fill",
  telegram: "ri-telegram-fill",
  instagram: "ri-instagram-line",
};

const PLATFORM_HINTS: [SocialPlatform, RegExp][] = [
  ["facebook", /facebook|\bfb\.com\b/],
  ["twitter", /twitter|\bx\.com\b/],
  ["youtube", /youtube|youtu\.be/],
  ["telegram", /telegram|\bt\.me\b/],
  ["instagram", /instagram/],
];

/**
 * Which platform a SocialNetwork row is. The admin stores `icon` as a full Remix class ("ri-facebook-fill",
 * "ri-twitter-x-fill") -- often a variant the subset font does not even contain -- while the old CMS stored the bare
 * name ("facebook"); looking the raw value up in a table therefore fell through to a generic chain-link icon.
 * The icon, title and link are all checked, so any of them is enough.
 */
export function resolveSocialPlatform(network: { icon?: string; title?: string; url?: string }): SocialPlatform | null {
  const haystack = `${network.icon ?? ""} ${network.title ?? ""} ${network.url ?? ""}`.toLowerCase();
  for (const [platform, pattern] of PLATFORM_HINTS) {
    if (pattern.test(haystack)) return platform;
  }
  return null;
}
