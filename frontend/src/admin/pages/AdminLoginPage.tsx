import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { clearTokens } from "@/api/client";
import { ApiError } from "@/types/api";
import { useAdminAuth } from "../AdminAuthContext";

const INPUT =
  "w-full h-12 px-4 rounded-lg border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500";

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const { refresh } = useAdminAuth();
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setStatus("loading");
    setError("");
    try {
      const user = await login({ username: String(fd.get("username")), password: String(fd.get("password")) });
      if (user.role !== "admin") {
        clearTokens();
        setStatus("error");
        setError("Bu hisobda administrator huquqi yo'q.");
        return;
      }
      await refresh();
      navigate("/admin");
    } catch (err) {
      setStatus("error");
      setError(err instanceof ApiError ? err.message : "Kirishda xatolik yuz berdi.");
    }
  }

  return (
    <div className="min-h-screen bg-background-100 lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,4fr)]">
      <aside className="hidden flex-col justify-between bg-primary-800 p-12 text-background-50 lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary-500 text-lg font-extrabold text-primary-950">F</div>
          <span className="font-heading text-lg font-bold">FJSTI Admin</span>
        </div>
        <div>
          <h2 className="font-heading text-4xl font-bold leading-tight">Saytni bu yerdan boshqarasiz</h2>
          <ul className="mt-8 space-y-4 text-background-50/80">
            {[
              ["ri-newspaper-line", "Yangilik va sahifalarni uch tilda yozing"],
              ["ri-image-line", "Rasm, PDF va hujjatlarni yuklang"],
              ["ri-inbox-line", "Kelgan murojaatlarni ko'ring"],
            ].map(([icon, text]) => (
              <li key={text} className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-background-50/10 text-lg">
                  <i className={icon} aria-hidden="true" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-background-50/50">Fargʻona jamoat salomatligi tibbiyot instituti</p>
      </aside>

      <main className="flex min-h-screen items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-800 text-lg font-extrabold text-secondary-500">F</div>
            <span className="font-heading text-lg font-bold text-foreground-950">FJSTI Admin</span>
          </div>
          <h1 className="font-heading text-2xl font-bold text-foreground-950">Kirish</h1>
          <p className="mb-6 mt-1 text-sm text-foreground-500">Login va parolingizni kiriting.</p>

          {status === "error" && (
            <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              <i className="ri-error-warning-line mt-0.5" aria-hidden="true" />
              {error}
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-username" className="mb-1.5 block text-sm font-medium text-foreground-700">Login</label>
              <input id="login-username" name="username" required autoFocus autoCapitalize="none" autoCorrect="off" spellCheck={false} autoComplete="username" className={INPUT} />
            </div>
            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-sm font-medium text-foreground-700">Parol</label>
              <input id="login-password" name="password" type="password" required autoComplete="current-password" className={INPUT} />
            </div>
            <button
              type="submit"
              disabled={status === "loading"}
              className="h-12 w-full cursor-pointer rounded-lg bg-primary-500 text-sm font-semibold text-background-50 hover:bg-primary-600 disabled:opacity-60"
            >
              {status === "loading" ? "Kirilmoqda..." : "Kirish"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
