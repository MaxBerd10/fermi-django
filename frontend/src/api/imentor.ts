import { imentorGet } from "./imentorClient";
import type {
  ImentorStatsResponse,
  ImentorSampleResponse,
  ImentorScenariosResponse,
  ImentorDocumentKind,
  ImentorDocumentListResponse,
  ImentorKeyDetail,
  ImentorTestDetail,
} from "@/types/imentor";
import type { ImentorLanguage } from "@/lib/imentorLanguage";

// Most departments in the catalog have no published tests/cases yet — stats' `by_subject`
// only lists subjects that actually have content, so pickers built from it never dead-end.
export async function getImentorTestStats() {
  const data = await imentorGet<ImentorStatsResponse>("v1/external/tests/stats/");
  return data.by_subject.filter((s) => (s.test_count || 0) > 0);
}

export async function getImentorKeyStats() {
  const data = await imentorGet<ImentorStatsResponse>("v1/external/keys/stats/");
  // The per-language numbers of the key stats count DOCUMENTS (a document holds several clinical cases, about 3), although
  // the pages show CASES; iMentor marks the unit with `totals.languages_unit` ("cases") once it reports cases. Until then
  // convert with the subject's own cases-per-document ratio, so a subject card and its list show the same number.
  const reportsCases = data.totals.languages_unit === "cases";
  return data.by_subject
    .filter((s) => (s.case_count || 0) > 0)
    .map((s) => {
      if (reportsCases || !s.languages || !s.case_count) return s;
      const casesPerDocument = Math.max(1, (s.questions_total || s.case_count) / s.case_count);
      const languages = Object.fromEntries(Object.entries(s.languages).map(([language, documents]) => [language, Math.round(documents * casesPerDocument)]));
      return { ...s, languages };
    });
}

/** `language`: draw the sample only from questions that exist in full in that language (fewer come back when fewer exist). */
export async function getImentorSampleQuestions(params: {
  subjectCode?: string;
  departmentCode?: string;
  topicCode?: string;
  count?: number;
  language?: ImentorLanguage;
}) {
  return imentorGet<ImentorSampleResponse>("v1/external/questions/sample/", {
    subject_code: params.subjectCode,
    department_code: params.departmentCode,
    topic_code: params.topicCode,
    count: params.count,
    language: params.language,
  });
}

export async function getImentorCaseScenarios(params: {
  subjectCode?: string;
  departmentCode?: string;
  count?: number;
  language?: ImentorLanguage;
}) {
  return imentorGet<ImentorScenariosResponse>("v1/external/keys/scenarios/", {
    subject_code: params.subjectCode,
    department_code: params.departmentCode,
    count: params.count,
    shuffle: false,
    language: params.language,
  });
}

/**
 * Every document of a subject (each one is a set of questions / cases on one topic of its syllabus), so the
 * topic list can show all of them -- unlike the random sample, which iMentor caps at 30 questions, and the
 * scenarios list, which stops at the first 50 cases. With `language`, only the documents that exist in that language
 * (their topic titles come back in that language too).
 */
export async function getImentorSubjectDocuments(kind: ImentorDocumentKind, subjectCode: string, language?: ImentorLanguage) {
  const first = await imentorGet<ImentorDocumentListResponse>(`v1/external/${kind}/`, { subject_code: subjectCode, page_size: 200, language });
  const documents = [...first.results];
  const pages = Math.min(Math.ceil(first.count / (first.page_size || 200)), 10);
  for (let page = 2; page <= pages; page += 1) {
    const next = await imentorGet<ImentorDocumentListResponse>(`v1/external/${kind}/`, { subject_code: subjectCode, page_size: 200, page, language });
    documents.push(...next.results);
  }
  return documents;
}

/** One test document with all its questions; with `language`, `payload.questions` are in that language when it exists. */
export function getImentorTest(id: number, language?: ImentorLanguage) {
  return imentorGet<ImentorTestDetail>(`v1/external/tests/${id}/`, { language });
}

/** One key document with all its clinical cases; with `language`, `payload.questions` are in that language when it exists. */
export function getImentorKey(id: number, language?: ImentorLanguage) {
  return imentorGet<ImentorKeyDetail>(`v1/external/keys/${id}/`, { language });
}
