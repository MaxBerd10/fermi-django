import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { apiClient } from "./client";

export interface HomePartner {
  id: number;
  name: string;
  url: string;
  icon: string;
}
export interface HomeProject {
  id: number;
  name: string;
  url: string | null;
  icon: string;
  img: string | null;
}
export interface HomeVoice {
  id: number;
  quote: string;
  name: string;
  meta: string;
}
export interface HomeFact {
  id: number;
  value: string;
  label: string;
}
export interface HomeWhy {
  id: number;
  title: string;
  desc: string;
  metric: string;
  metricLabel: string;
}
export interface HomeSections {
  partners: HomePartner[];
  projects: HomeProject[];
  voices: HomeVoice[];
  facts: HomeFact[];
  why: HomeWhy[];
}

// One request per language per page view: four home sections share it. null = the request failed, and each
// section then shows its built-in copy of the same content instead of an empty block.
const requests = new Map<string, Promise<HomeSections | null>>();

function loadHomeSections(lang: string): Promise<HomeSections | null> {
  let request = requests.get(lang);
  if (!request) {
    request = apiClient
      .get<HomeSections>("home-sections")
      .then(({ data }) => data)
      .catch(() => null);
    requests.set(lang, request);
  }
  return request;
}

/** undefined while loading, null if the request failed, else the editable lists. */
export function useHomeSections(): HomeSections | null | undefined {
  const { i18n } = useTranslation();
  const lang = (i18n.resolvedLanguage || i18n.language || "uz").slice(0, 2);
  const [sections, setSections] = useState<HomeSections | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;
    loadHomeSections(lang).then((data) => {
      if (!cancelled) setSections(data);
    });
    return () => {
      cancelled = true;
    };
  }, [lang]);

  return sections;
}
