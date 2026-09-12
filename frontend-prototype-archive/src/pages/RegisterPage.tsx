import { useState } from "react";
import * as authApi from "../api/auth";

const inputClass =
  "w-full rounded-lg border border-primary-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500/15 focus:border-primary-500";

export function RegisterPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "sent" | "error">("idle");
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setStatus("loading");
    try {
      await authApi.register(String(fd.get("username")), String(fd.get("email")), String(fd.get("password")));
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Xatolik yuz berdi");
    }
  }

  if (status === "sent") {
    return (
      <div className="mx-auto max-w-sm px-6 py-16">
        <div className="rounded-xl bg-emerald-50 p-4 text-emerald-800">
          Hisobingizni faollashtirish uchun emailingizga havola yubordik.
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm px-6 py-16">
      <div className="page-card p-6">
        <h1 className="mb-6 font-display text-2xl font-bold text-primary-900">Ro'yxatdan o'tish</h1>
        {error && <div className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <form onSubmit={onSubmit} className="space-y-4">
          <input name="username" placeholder="Foydalanuvchi nomi" required className={inputClass} />
          <input name="email" type="email" placeholder="Email" required className={inputClass} />
          <input name="password" type="password" placeholder="Parol" required minLength={8} className={inputClass} />
          <button type="submit" disabled={status === "loading"} className="uni-btn w-full">
            {status === "loading" ? "Yuborilmoqda..." : "Ro'yxatdan o'tish"}
          </button>
        </form>
      </div>
    </div>
  );
}
