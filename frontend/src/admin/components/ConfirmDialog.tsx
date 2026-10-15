import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";

export interface ConfirmOptions {
  title: string;
  message?: ReactNode;
  confirmLabel?: string;
  /** Red confirm button, and the focus starts on "Bekor qilish" so Enter cannot delete by accident. */
  danger?: boolean;
}

type Ask = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmContext = createContext<Ask | null>(null);

/** Our own confirmation window (instead of the browser's grey one): says what will happen in plain words and
 *  makes the dangerous choice look dangerous. Use `const confirm = useConfirm(); if (!(await confirm({...}))) return;`. */
export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<{ options: ConfirmOptions; resolve: (ok: boolean) => void } | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const okRef = useRef<HTMLButtonElement>(null);

  const ask = useCallback<Ask>(
    (options) =>
      new Promise<boolean>((resolve) => {
        setPending({ options, resolve });
      }),
    [],
  );

  function close(ok: boolean) {
    pending?.resolve(ok);
    setPending(null);
  }

  useEffect(() => {
    if (!pending) return;
    (pending.options.danger ? cancelRef : okRef).current?.focus();
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        pending?.resolve(false);
        setPending(null);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pending]);

  const options = pending?.options;

  return (
    <ConfirmContext.Provider value={ask}>
      {children}
      {options && (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-primary-950/50 px-4" onMouseDown={() => close(false)}>
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
            className="w-full max-w-md rounded-xl bg-background-50 p-6 shadow-2xl"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-4">
              <span
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-xl ${
                  options.danger ? "bg-red-50 text-red-600" : "bg-primary-50 text-primary-600"
                }`}
              >
                <i className={options.danger ? "ri-delete-bin-line" : "ri-question-line"} aria-hidden="true" />
              </span>
              <div className="min-w-0">
                <h2 id="confirm-title" className="font-heading text-base font-bold text-foreground-950">{options.title}</h2>
                {options.message && <div className="mt-1.5 text-sm leading-relaxed text-foreground-600">{options.message}</div>}
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button
                ref={cancelRef}
                type="button"
                onClick={() => close(false)}
                className="h-10 cursor-pointer rounded-lg border border-background-300 px-4 text-sm font-medium text-foreground-700 hover:bg-background-100"
              >
                Bekor qilish
              </button>
              <button
                ref={okRef}
                type="button"
                onClick={() => close(true)}
                className={`h-10 cursor-pointer rounded-lg px-5 text-sm font-semibold text-background-50 ${
                  options.danger ? "bg-red-600 hover:bg-red-700" : "bg-primary-500 hover:bg-primary-600"
                }`}
              >
                {options.confirmLabel ?? "Ha"}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

/** Outside the admin layout (should not happen) it falls back to the browser's own confirm. */
export function useConfirm(): Ask {
  const ask = useContext(ConfirmContext);
  return ask ?? (async (options) => window.confirm(options.title));
}
