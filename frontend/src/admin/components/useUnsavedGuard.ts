import { useEffect } from "react";

/** Asks the browser to confirm before the tab is closed or reloaded while the form has unsaved edits. */
export function useUnsavedGuard(dirty: boolean) {
  useEffect(() => {
    if (!dirty) return;
    function onBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
      e.returnValue = "";
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [dirty]);
}

/** "14:32" in Tashkent time, for the "Saqlandi" line. */
export function nowLabel(): string {
  return new Intl.DateTimeFormat("ru-RU", { timeZone: "Asia/Tashkent", hour: "2-digit", minute: "2-digit" }).format(new Date());
}
