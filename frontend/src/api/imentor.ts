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

// Most departments in the catalog have no published tests/cases yet — stats' `by_subject`
// only lists subjects that actually have content, so pickers built from it never dead-end.
export async function getImentorTestStats() {
  const data = await imentorGet<ImentorStatsResponse>("v1/external/tests/stats/");
  return data.by_subject.filter((s) => (s.test_count || 0) > 0);
}

export async function getImentorKeyStats() {
  const data = await imentorGet<ImentorStatsResponse>("v1/external/keys/stats/");
  return data.by_subject.filter((s) => (s.case_count || 0) > 0);
}

export async function getImentorSampleQuestions(params: {
  subjectCode?: string;
  departmentCode?: string;
  topicCode?: string;
  count?: number;
}) {
  return imentorGet<ImentorSampleResponse>("v1/external/questions/sample/", {
    subject_code: params.subjectCode,
    department_code: params.departmentCode,
    topic_code: params.topicCode,
    count: params.count,
  });
}

export async function getImentorCaseScenarios(params: {
  subjectCode?: string;
  departmentCode?: string;
  count?: number;
}) {
  return imentorGet<ImentorScenariosResponse>("v1/external/keys/scenarios/", {
    subject_code: params.subjectCode,
    department_code: params.departmentCode,
    count: params.count,
    shuffle: false,
  });
}

/**
 * Every document of a subject (each one is a set of questions / cases on one topic of its syllabus), so the
 * topic list can show all of them -- unlike the random sample, which iMentor caps at 30 questions, and the
 * scenarios list, which stops at the first 50 cases.
 */
export async function getImentorSubjectDocuments(kind: ImentorDocumentKind, subjectCode: string) {
  const first = await imentorGet<ImentorDocumentListResponse>(`v1/external/${kind}/`, { subject_code: subjectCode, page_size: 200 });
  const documents = [...first.results];
  const pages = Math.min(Math.ceil(first.count / (first.page_size || 200)), 10);
  for (let page = 2; page <= pages; page += 1) {
    const next = await imentorGet<ImentorDocumentListResponse>(`v1/external/${kind}/`, { subject_code: subjectCode, page_size: 200, page });
    documents.push(...next.results);
  }
  return documents;
}

/** One test document with all its questions (and their ru/en translations). */
export function getImentorTest(id: number) {
  return imentorGet<ImentorTestDetail>(`v1/external/tests/${id}/`);
}

/** One key document with all its clinical cases. */
export function getImentorKey(id: number) {
  return imentorGet<ImentorKeyDetail>(`v1/external/keys/${id}/`);
}
