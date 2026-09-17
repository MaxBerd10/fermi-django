import { apiClient } from "./client";
import type { ResultCategory, ResultsPageInfo } from "../types/content";

export async function getAdmissionResults() {
  const { data } = await apiClient.get<ResultCategory[]>("admission-results");
  return data;
}

export async function getAdmissionResultsPage() {
  const { data } = await apiClient.get<ResultsPageInfo>("admission-results-page");
  return data;
}
