import { FORM_FIELD, FORM_LABEL, FORM_TEXTAREA } from "@/lib/formFields";
import { useRef, useState } from "react";
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
// Mirrors MAX_VISITOR_UPLOAD_BYTES in apps/forms/views.py -- checked here too so a big file fails
// instantly with a clear message instead of after a slow upload the server then refuses.
const MAX_FILE_BYTES = 20 * 1024 * 1024;

export default function ContestApplicationForm({ contestId }: { contestId: number }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [error, setError] = useState("");
  const [ticketId, setTicketId] = useState<number | null>(null);
  // A contest entry normally comes with a document (a presentation, a project description). The file stays optional, but
  // an application sent without one used to look just like a complete one -- so the first time the visitor presses
  // "send" with no file, the form says so and asks (10 of 18 applicants of the first InnoMix intake sent no file).
  const [askNoFile, setAskNoFile] = useState(false);
  const sendWithoutFile = useRef(false);
  const formRef = useRef<HTMLFormElement>(null);

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

    const file = formData.get("file") as File;

    if ((!file || file.size === 0) && !sendWithoutFile.current) {
      setAskNoFile(true);
      setStatus("idle");
      setError("");
      return;
    }
    sendWithoutFile.current = false;
    setAskNoFile(false);
    setStatus("loading");
    setError("");

    if (file && file.size > MAX_FILE_BYTES) {
      setStatus("error");
      setError(t("contest.fileTooLarge"));
      return;
    }

    try {
      const res = await submitContestApplication({
        contestId,
        fullName: String(formData.get("fullName") || ""),
        phone: String(formData.get("phone") || ""),
        email: String(formData.get("email") || ""),
        message: String(formData.get("message") || ""),
        file: file && file.size > 0 ? file : null,
      });
      setTicketId(res.number ?? res.id);
      setStatus("success");
      form.reset();
    } catch (err) {
      setStatus("error");
      if (err instanceof ApiError && err.status === 413) setError(t("contest.fileTooLarge"));
      else setError(err instanceof ApiError ? err.message : t("contest.submitError"));
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
        <form ref={formRef} onSubmit={handleSubmit} className="space-y-3.5">
          <div className="absolute opacity-0 pointer-events-none">
            <input type="text" name="company_alt" tabIndex={-1} autoComplete="off" aria-hidden="true" readOnly className="sr-only" />
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className={FORM_LABEL}>
                {t("contest.fullName")} <span className="text-red-500">*</span>
              </label>
              <input
                name="fullName"
                type="text"
                required
                className={FORM_FIELD}
                placeholder={t("contest.fullNamePlaceholder")}
              />
            </div>
            <div>
              <label className={FORM_LABEL}>
                {t("contest.phoneLabel")} <span className="text-red-500">*</span>
              </label>
              <input
                name="phone"
                type="tel"
                required
                className={FORM_FIELD}
                placeholder="+998 90 123 45 67"
              />
            </div>
          </div>

          <div>
            <label className={FORM_LABEL}>
              {t("contest.emailLabel")} <span className="text-red-500">*</span>
            </label>
            <input
              name="email"
              type="email"
              required
              className={FORM_FIELD}
              placeholder="email@example.com"
            />
          </div>

          <div>
            <label className={FORM_LABEL}>{t("contest.messageLabel")}</label>
            <textarea
              name="message"
              rows={4}
              maxLength={2000}
              className={FORM_TEXTAREA}
              placeholder={t("contest.messagePlaceholder")}
            />
          </div>

          <div>
            <label className={FORM_LABEL}>{t("contest.fileLabel")}</label>
            <input
              name="file"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.ppt,.pptx"
              onChange={() => setAskNoFile(false)}
              className="w-full text-sm text-foreground-600 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:bg-primary-50 file:text-primary-700 file:text-sm"
            />
            {askNoFile && (
              <div role="alert" className="mt-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                <p>{t("contest.noFileWarning")}</p>
                <button
                  type="button"
                  onClick={() => {
                    sendWithoutFile.current = true;
                    formRef.current?.requestSubmit();
                  }}
                  className="mt-2 cursor-pointer font-semibold underline underline-offset-2 hover:text-amber-950"
                >
                  {t("contest.sendWithoutFile")}
                </button>
              </div>
            )}
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
