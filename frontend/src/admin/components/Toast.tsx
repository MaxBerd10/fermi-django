import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";

type Tone = "success" | "error" | "info";

interface ToastItem {
  id: number;
  tone: Tone;
  text: string;
}

interface ToastApi {
  success: (text: string) => void;
  error: (text: string) => void;
  info: (text: string) => void;
}

const ToastContext = createContext<ToastApi | null>(null);

const TONE_STYLE: Record<Tone, { box: string; icon: string }> = {
  success: { box: "border-green-200 bg-green-50 text-green-900", icon: "ri-checkbox-circle-line text-green-600" },
  error: { box: "border-red-200 bg-red-50 text-red-900", icon: "ri-error-warning-line text-red-600" },
  info: { box: "border-primary-200 bg-primary-50 text-primary-900", icon: "ri-information-line text-primary-600" },
};

/** Short messages that appear over the page for a few seconds ("Saqlandi", "Xatolik ..."), so they are seen
 *  even when the form is scrolled far from where the message would otherwise be printed. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => setItems((list) => list.filter((t) => t.id !== id)), []);

  const push = useCallback(
    (tone: Tone, text: string) => {
      const id = nextId.current++;
      setItems((list) => [...list.slice(-3), { id, tone, text }]);
      window.setTimeout(() => dismiss(id), tone === "error" ? 9000 : 3500);
    },
    [dismiss],
  );

  const api = useMemo<ToastApi>(
    () => ({
      success: (text) => push("success", text),
      error: (text) => push("error", text),
      info: (text) => push("info", text),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        className="pointer-events-none fixed inset-x-0 bottom-20 z-[70] flex flex-col items-center gap-2 px-4 lg:bottom-6 lg:items-end lg:px-6"
        aria-live="polite"
      >
        {items.map((item) => (
          <div
            key={item.id}
            role={item.tone === "error" ? "alert" : "status"}
            className={`pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-lg ${TONE_STYLE[item.tone].box}`}
          >
            <i className={`${TONE_STYLE[item.tone].icon} mt-0.5 text-lg`} aria-hidden="true" />
            <span className="flex-1 leading-snug">{item.text}</span>
            <button
              type="button"
              onClick={() => dismiss(item.id)}
              className="-mr-1 flex h-6 w-6 shrink-0 cursor-pointer items-center justify-center rounded opacity-60 hover:opacity-100"
              aria-label="Yopish"
            >
              <i className="ri-close-line" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

const SILENT: ToastApi = { success: () => {}, error: () => {}, info: () => {} };

export function useToast(): ToastApi {
  return useContext(ToastContext) ?? SILENT;
}
