/**
 * The few things a Telegram Mini App must do with Telegram, written out here instead of loading Telegram's own script
 * (a third-party script inside our own origin would be able to read everything this origin stores, administrator
 * sessions included).
 *
 *  - Telegram puts what it knows about the opening in the address fragment: `#tgWebAppData=<initData>&tgWebAppThemeParams=...`.
 *    `initData` is the signed proof of who the person is: the server checks the signature (apps/telegram_bot/webapp.py).
 *  - To tell Telegram things ("ready", "expand to full height", "ask before closing") the page posts an event: through
 *    TelegramWebviewProxy in the phone apps, window.external.notify on Windows, postMessage to the parent on Telegram Web.
 */
interface ThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

declare global {
  interface Window {
    TelegramWebviewProxy?: { postEvent: (eventType: string, eventData: string) => void };
  }
}

const STORAGE_KEY = "fjsti-tg-launch";

function readLaunch(): { initData: string; theme: ThemeParams } {
  const fromHash = (hash: string) => {
    const params = new URLSearchParams(hash.replace(/^#/, ""));
    const initData = params.get("tgWebAppData") || "";
    let theme: ThemeParams = {};
    try {
      theme = JSON.parse(params.get("tgWebAppThemeParams") || "{}");
    } catch {
      theme = {};
    }
    return { initData, theme };
  };
  let launch = fromHash(window.location.hash);
  try {
    if (launch.initData) window.sessionStorage.setItem(STORAGE_KEY, window.location.hash);
    else launch = fromHash(window.sessionStorage.getItem(STORAGE_KEY) || "");
  } catch {
    /* blocked storage: the fragment alone has to do */
  }
  return launch;
}

const launch = typeof window === "undefined" ? { initData: "", theme: {} as ThemeParams } : readLaunch();

/** The signed string to send as `Authorization: tma <initData>`; empty when the page was not opened by Telegram. */
export const initData = launch.initData;
export const theme: ThemeParams = launch.theme;

export function postEvent(eventType: string, eventData: Record<string, unknown> | null = null): void {
  try {
    if (window.TelegramWebviewProxy?.postEvent) {
      window.TelegramWebviewProxy.postEvent(eventType, JSON.stringify(eventData));
    } else if (typeof (window.external as { notify?: unknown } | undefined)?.notify === "function") {
      (window.external as unknown as { notify: (message: string) => void }).notify(JSON.stringify({ eventType, eventData }));
    } else if (window.parent !== window) {
      window.parent.postMessage(JSON.stringify({ eventType, eventData }), "*");
    }
  } catch {
    /* not inside Telegram (a browser tab): nothing to tell */
  }
}

export const ready = () => postEvent("web_app_ready");
export const expand = () => postEvent("web_app_expand");
export const close = () => postEvent("web_app_close");
/** While true, Telegram asks "Close anyway?" before the person leaves: used while a form holds unsent work. */
export const confirmClosing = (need: boolean) => postEvent("web_app_setup_closing_behavior", { need_confirmation: need });
