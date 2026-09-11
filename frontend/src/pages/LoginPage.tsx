import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");
  const { refresh } = useAuth();
  const navigate = useNavigate();

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setStatus("loading");
    try {
      await authApi.login(String(fd.get("username")), String(fd.get("password")));
      await refresh();
      navigate("/");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Login yoki parol noto'g'ri");
    }
  }

  return (
    <div className="mx-auto max-w-sm px-6 py-16">
      <h1 className="mb-6 text-2xl font-bold text-slate-900">Kirish</h1>
      {error && <div className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      <form onSubmit={onSubmit} className="space-y-4">
        <input name="username" placeholder="Foydalanuvchi nomi" required className="w-full rounded-lg border border-slate-300 px-3 py-2" />
        <input name="password" type="password" placeholder="Parol" required className="w-full rounded-lg border border-slate-300 px-3 py-2" />
        <button
          type="submit"
          disabled={status === "loading"}
          className="w-full rounded-lg bg-slate-900 py-2 font-medium text-white disabled:opacity-60"
        >
          {status === "loading" ? "Kirilmoqda..." : "Kirish"}
        </button>
      </form>
    </div>
  );
}
