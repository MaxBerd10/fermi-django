import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { isSupportedLang, loadMessages, type SupportedLang } from './local/index';
import { fetchSiteTexts, readInjectedSiteTexts } from '../lib/siteTexts';

// Matches i18next-browser-languagedetector's default localStorage key —
// kept in sync manually (see resolveInitialLanguage below) so we can
// synchronously decide which single language bundle to fetch, before
// i18next itself has even started initializing.
const STORAGE_KEY = 'i18nextLng';

function resolveInitialLanguage(): SupportedLang {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isSupportedLang(stored)) return stored;
  } catch {
    // localStorage unavailable (private mode, disabled storage, etc.) — fall
    // through to the site's long-standing default below.
  }
  // Legacy site always defaulted to 'uz' regardless of browser/OS language.
  return 'uz';
}

const initialLang = resolveInitialLanguage();

// Texts edited in the admin panel; present when the Node server put them into index.html (the normal case).
const injectedSiteTexts = readInjectedSiteTexts();

// Only the active language's translation bundle loads up front — the other
// two are dead weight on every page view otherwise. The language switcher
// (see Navbar's changeLanguage) writes the new choice to localStorage and
// does a full page reload, so the next load picks it up here; no in-session
// language switching needs to happen, which is what would otherwise require
// lazy-loading a second bundle mid-session.
loadMessages(initialLang)
  .then((translation) =>
    i18n.use(initReactI18next).init({
      lng: initialLang,
      fallbackLng: 'uz',
      debug: false,
      // i18next prints an unconditional console.info() promoting its own
      // Locize product on every init, regardless of `debug` -- unrelated to
      // this project, and Lighthouse's Best Practices "errors logged to
      // console" audit flags it on every single page load in production.
      showSupportNotice: false,
      resources: {
        // the admin-edited texts lie over the built-in wording, language by language
        [initialLang]: { translation: { ...translation, ...(injectedSiteTexts?.[initialLang] ?? {}) } },
      },
      interpolation: {
        escapeValue: false,
      },
    })
  )
  .then(() => {
    document.documentElement.lang = i18n.language.slice(0, 2);
    if (injectedSiteTexts) return;
    // No data block (dev server, or Django was unreachable when the page was served): fetch the edited texts once.
    return fetchSiteTexts().then((texts) => {
      const own = texts?.[initialLang];
      if (own && Object.keys(own).length) {
        i18n.addResourceBundle(initialLang, 'translation', own, true, true);
        void i18n.changeLanguage(initialLang); // re-renders what is already on screen
      }
    });
  });

// Keeps <html lang> in sync with the active UI language — index.html hardcodes
// lang="uz" for the initial (pre-JS) load, but never updated after a language
// switch, which is wrong for screen readers and search engines alike.
i18n.on('languageChanged', (lng) => {
  document.documentElement.lang = lng.slice(0, 2);
});

export default i18n;
