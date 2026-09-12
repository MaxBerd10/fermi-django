import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as authApi from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export function VerifyEmailPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");
  const { refresh } = useAuth();

  useEffect(() => {
    if (!uid || !token) return;
    authApi
      .verifyEmail(uid, token)
      .then(async () => {
        await refresh();
        setStatus("success");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Havola noto'g'ri");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uid, token]);

  return (
    <div className="mx-auto max-w-sm px-6 py-16 text-center">
      {status === "loading" && <p className="text-slate-500">Tekshirilmoqda...</p>}
      {status === "success" && (
        <div className="rounded-xl bg-emerald-50 p-4 text-emerald-800">
          Hisobingiz faollashtirildi. Tizimga kirdingiz.
        </div>
      )}
      {status === "error" && <div className="rounded-xl bg-red-50 p-4 text-red-700">{message}</div>}
    </div>
  );
}
