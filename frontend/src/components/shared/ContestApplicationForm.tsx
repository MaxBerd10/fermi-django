import { useState } from "react";
import { useTranslation } from "react-i18next";
import { submitContestApplication } from "@/api/forms";
import { ApiError } from "@/types/api";

/**
 * "Ariza topshirish" -- the document-intake form for a "Tanlovlar"
 * (contests/announcements) NewsPost, rendered by detail/page.tsx only
 * when the article's category is "tanlovlar". No login/account system:
 * same anonymous-submission shape as the /virtual-qabulxona form (see
 * apps.forms.models.ContestSubmission), just scoped to one announcement
 * via `contestId`.
 */
export default function ContestApplicationForm({ contestId }: { contestId: number }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [error, setError] = useState("");
  const [ticketId, setTicketId] = useState<number | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);

    // Honeypot -- same anti-spam pattern as the virtual-qabulxona form.
    const honey = (formData.get("company_alt") as string)?.trim();
    if (honey) {
      setStatus("success");
      form.reset();
      return;
    }

    setStatus("loading");
    setError("");

    const file = formData.get("file") as File;

    try {
      const res = await submitContestApplication({
        contestId,
        fullName: String(formData.get("fullName") || ""),
        phone: String(formData.get("phone") || ""),
        email: String(formData.get("email") || ""),
        message: String(formData.get("message") || ""),
        file: file && file.size > 0 ? file : null,
      });
      setTicketId(res.id);
      setStatus("success");
      form.reset();
    } catch (err) {
      setStatus("error");
      setError(err instanceof ApiError ? err.message : t("contest.submitError"));
    }
  };

  return (
    <div className="page-card p-4 md:p-5 mt-6">
      <h2 className="font-heading text-lg font-semibold text-foreground-900 mb-1">{t("contest.formTitle")}</h2>
      <p className="text-sm text-foreground-600 mb-4">{t("contest.formSubtitle")}</p>

      {status === "success" && (
        <div className="mb-4 p-4 rounded-2xl bg-green-50 border border-green-200/80 text-green-800 text-sm flex items-start gap-3">
          <i className="ri-checkbox-circle-line w-5 h-5 flex items-center justify-center text-green-600 flex-shrink-0" />
          <div>
            <p className="font-semibold">{t("contest.successTitle")}</p>
            {ticketId && <p>{t("contest.ticketNote", { id: ticketId })}</p>}
          </div>
        </div>
      )}

      {status === "error" && error && (
        <div className="mb-4 p-4 rounded-2xl bg-red-50 border border-red-200/80 text-red-800 text-sm flex items-start gap-3">
          <i className="ri-error-warning-line w-5 h-5 flex items-center justify-center text-red-600 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {status !== "success" && (
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="absolute opacity-0 pointer-events-none">
            <input type="text" name="company_alt" tabIndex={-1} autoComplete="off" aria-hidden="true" readOnly className="sr-only" />
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1">
                {t("contest.fullName")} <span className="text-red-500">*</span>
              </label>
              <input
                name="fullName"
                type="text"
                required
                className="w-full h-10 px-3 page-input text-sm focus:outline-none focus:border-primary-500"
                placeholder={t("contest.fullNamePlaceholder")}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1">
                {t("contest.phoneLabel")} <span className="text-red-500">*</span>
              </label>
              <input
                name="phone"
                type="tel"
                required
                className="w-full h-10 px-3 page-input text-sm focus:outline-none focus:border-primary-500"
                placeholder="+998 90 123 45 67"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-700 mb-1">
              {t("contest.emailLabel")} <span className="text-red-500">*</span>
            </label>
            <input
              name="email"
              type="email"
              required
              className="w-full h-10 px-3 page-input text-sm focus:outline-none focus:border-primary-500"
              placeholder="email@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-700 mb-1.5">{t("contest.messageLabel")}</label>
            <textarea
              name="message"
              rows={4}
              maxLength={2000}
              className="w-full px-4 py-3 page-input text-sm focus:outline-none focus:border-primary-500 resize-y"
              placeholder={t("contest.messagePlaceholder")}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground-700 mb-1.5">{t("contest.fileLabel")}</label>
            <input
              name="file"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx"
              className="w-full text-sm text-foreground-600 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-primary-50 file:text-primary-700 file:text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 h-12 px-8 rounded-xl bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer whitespace-nowrap transition-colors disabled:opacity-60"
          >
            {status === "loading" ? (
              <>
                <i className="ri-loader-4-line w-4 h-4 flex items-center justify-center animate-spin" />
                {t("contact.sending")}
              </>
            ) : (
              <>
                <i className="ri-send-plane-line w-4 h-4 flex items-center justify-center" />
                {t("contest.submit")}
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}
