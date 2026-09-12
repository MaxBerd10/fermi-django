import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import * as authApi from "../api/auth";
import { useAuth } from "../auth/AuthContext";

const inputClass =
  "w-full rounded-lg border border-primary-100 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500/15 focus:border-primary-500";

export function ResetPasswordPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");
  const { refresh } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!uid || !token) return;
    const password = String(new FormData(e.currentTarget).get("password"));
    setStatus("loading");
    try {
      await authApi.confirmPasswordReset(uid, token, password);
      await refresh();
      navigate("/");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Havola eskirgan yoki noto'g'ri");
    }
  }

  return (
    <div className="mx-auto max-w-sm px-6 py-16">
      <div className="page-card p-6">
        <h1 className="mb-6 font-display text-2xl font-bold text-primary-900">Yangi parol</h1>
        {error && <div className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <form onSubmit={onSubmit} className="space-y-4">
          <input name="password" type="password" placeholder="Yangi parol" required minLength={8} className={inputClass} />
          <button type="submit" disabled={status === "loading"} className="uni-btn w-full">
            {status === "loading" ? "Yangilanmoqda..." : "Parolni yangilash"}
          </button>
        </form>
      </div>
    </div>
  );
}
