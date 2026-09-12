/**
 * Integrations that depend on secrets/infra this deployment doesn't have yet
 * (no OpenAI key, no Telegram bot session, no iMentor API key) — off by
 * default so the site never renders a dead button or silently 404s against
 * a proxy route that isn't there. Flip one on locally by setting the matching
 * VITE_FEATURE_* env var to "true" once real credentials exist.
 *
 * Each flag is consumed at a different seam depending on what "off" needs to
 * mean for that feature — see the call sites (Layout.tsx + 5 AiPanel call
 * sites for `ai`; api/telegram.ts for `telegram`; Navbar.tsx + api/imentorClient.ts
 * for `imentor`) rather than one central switch, because a chat widget and a
 * background news feed and a hard-linked exam portal each fail differently
 * when they're not actually available.
 */
export const FEATURES = {
  ai: import.meta.env.VITE_FEATURE_AI === "true",
  telegram: import.meta.env.VITE_FEATURE_TELEGRAM === "true",
  imentor: import.meta.env.VITE_FEATURE_IMENTOR === "true",
} as const;
