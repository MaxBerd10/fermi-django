import { useState } from "react";
import * as authApi from "../api/auth";

const inputClass =
  "w-full rounded-lg border border-primary-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500/15 focus:border-primary-500";

export function ForgotPasswordPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "sent">("idle");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const email = String(new FormData(e.currentTarget).get("email"));
    setStatus("loading");
    await authApi.requestPasswordReset(email);
    setStatus("sent");
  }

  if (status === "sent") {
    return (
      <div className="mx-auto max-w-sm px-6 py-16">
        <div className="rounded-xl bg-emerald-50 p-4 text-emerald-800">
          Agar bu email ro'yxatdan o'tgan bo'lsa, parolni tiklash havolasi yuborildi.
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm px-6 py-16">
      <div className="page-card p-6">
        <h1 className="mb-2 font-display text-2xl font-bold text-primary-900">Parolni tiklash</h1>
        <p className="mb-6 text-sm text-foreground-600">Emailingizni kiriting, tiklash havolasini yuboramiz.</p>
        <form onSubmit={onSubmit} className="space-y-4">
          <input name="email" type="email" placeholder="Email" required className={inputClass} />
          <button type="submit" disabled={status === "loading"} className="uni-btn w-full">
            {status === "loading" ? "Yuborilmoqda..." : "Havola yuborish"}
          </button>
        </form>
      </div>
    </div>
  );
}
