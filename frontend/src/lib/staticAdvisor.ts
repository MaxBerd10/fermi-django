/**
 * Answers for the two "advisor" boxes on the home page (which faculty suits me / PathFinder from free text)
 * that need no AI service: keywords in the visitor's own words pick the faculty, and the answer is built from
 * facts the site already states (the four faculties, the admission steps, the study levels). It works offline from
 * the OpenAI proxy, so the boxes never answer "temporarily unavailable"; when the AI service is switched on, these
 * answers are also what a failed AI call falls back to.
 *
 * No medical advice is given and nothing is invented: when no keyword matches, the answer says so and points to
 * the faculty list, PathFinder and the virtual reception.
 */

type Lang = "uz" | "ru" | "en";
type L10n = Record<Lang, string>;
type FacultyKey = "davolash" | "profilaktika" | "xalqaro" | "pediatriya";
type LevelKey = "bakalavriat" | "magistratura" | "ordinatura" | "doktorantura";

export function toLang(lang: string): Lang {
  const short = (lang || "uz").slice(0, 2);
  return short === "ru" || short === "en" ? short : "uz";
}

interface Faculty {
  slug: string;
  name: L10n;
  /** what the faculty is (the site's own description of it) */
  about: L10n;
  /** stems looked for in the visitor's text (uz / ru / en, lower case, apostrophes removed) */
  keywords: string[];
  related: FacultyKey[];
}

const FACULTIES: Record<FacultyKey, Faculty> = {
  davolash: {
    slug: "davolash-ishi",
    name: { uz: "Davolash ishi", ru: "Лечебное дело", en: "General Medicine" },
    about: {
      uz: "umumiy tibbiyot va klinik yoʻnalishda tayyorlaydi — bemor bilan ishlash, tashxis va davolash koʻnikmalari",
      ru: "готовит по общей медицине и клиническому направлению — работа с пациентом, диагностика и лечение",
      en: "trains in general medicine and the clinical track — working with patients, diagnosis and treatment",
    },
    keywords: [
      "davola", "shifokor", "vrach", "klinik", "klinika", "jarroh", "terapevt", "kardiolog", "nevrolog", "bemor", "tashxis", "umumiy tibbiyot", "xirurg",
      "лечебн", "лечи", "врач", "хирург", "клиник", "терапевт", "кардиолог", "пациент", "диагност", "лечени",
      "doctor", "physician", "surgeon", "surgery", "clinic", "patient", "general medicine", "cardio", "treat",
    ],
    related: ["pediatriya", "profilaktika"],
  },
  profilaktika: {
    slug: "tibbiy-profilaktika-va-jamoat-salomatligi-fakulteti",
    name: {
      uz: "Tibbiy profilaktika va jamoat salomatligi",
      ru: "Медицинская профилактика и общественное здоровье",
      en: "Medical Prevention and Public Health",
    },
    about: {
      uz: "epidemiologiya, profilaktika va aholi salomatligi boʻyicha tayyorlaydi",
      ru: "готовит по эпидемиологии, профилактике и здоровью населения",
      en: "trains in epidemiology, prevention and population health",
    },
    keywords: [
      "profilakt", "epidemiolog", "jamoat salomat", "gigiyen", "sanitar", "ekolog", "ovqatlanish", "aholi salomat", "menejment", "boshqaruv", "ssv", "infeksiya", "emlash",
      "профилакт", "эпидемиолог", "гигиен", "санитар", "эколог", "общественн", "здоровье населения", "менеджмент", "инфекц", "вакцин",
      "prevent", "epidemiolog", "public health", "hygiene", "sanitation", "nutrition", "ecolog", "management", "infection", "vaccin",
    ],
    related: ["davolash", "xalqaro"],
  },
  xalqaro: {
    slug: "xalqaro-fakultet",
    name: { uz: "Xalqaro fakultet", ru: "Международный факультет", en: "International Faculty" },
    about: {
      uz: "xorijiy talabalar va xalqaro dasturlar uchun moʻljallangan, koʻp tilli taʼlim muhiti bilan",
      ru: "предназначен для иностранных студентов и международных программ, с многоязычной образовательной средой",
      en: "is meant for foreign students and international programmes, with a multilingual learning environment",
    },
    keywords: [
      "xalqaro", "xorij", "chet el", "ingliz", "rus tili", "almashinuv", "global", "tillar",
      "международн", "иностран", "за рубеж", "английск", "обмен", "зарубеж",
      "international", "abroad", "foreign", "english", "exchange", "overseas",
    ],
    related: ["davolash", "pediatriya"],
  },
  pediatriya: {
    slug: "pediatriya-fakulteti",
    name: { uz: "Pediatriya fakulteti", ru: "Факультет педиатрии", en: "Faculty of Pediatrics" },
    about: {
      uz: "bolalar salomatligi va pediatriya boʻyicha tayyorlaydi — yoshga mos diagnostika, davolash, profilaktika va oilaviy maslahat",
      ru: "готовит по детскому здоровью и педиатрии — диагностика, лечение и профилактика с учётом возраста, семейное консультирование",
      en: "trains in children's health and pediatrics — age-appropriate diagnosis, treatment, prevention and family counselling",
    },
    keywords: [
      "bolalar", "bola ", "bolalik", "pediatr", "chaqaloq", "neonatolog", "yosh bola",
      "детск", "детей", "дети", "детям", "детьми", "педиатр", "ребен", "ребён", "новорожд", "младен",
      "child", "pediatric", "paediatric", "kids", "infant", "newborn", "baby", "babies",
    ],
    related: ["davolash", "profilaktika"],
  },
};

/** the order the four faculties are listed in */
const FACULTY_ORDER: FacultyKey[] = ["davolash", "profilaktika", "xalqaro", "pediatriya"];
/** on equal scores the more specific faculty wins ("a children's doctor" is Pediatrics, not General Medicine) */
const SPECIFICITY: FacultyKey[] = ["pediatriya", "xalqaro", "profilaktika", "davolash"];

function normalize(text: string): string {
  return ` ${String(text || "").toLowerCase().replace(/[ʻʼ’‘`']/g, "")} `;
}

/** faculties that the text points to, best first (an empty list when nothing in it matches) */
function rankFaculties(text: string): FacultyKey[] {
  const haystack = normalize(text);
  return SPECIFICITY.map((key) => ({ key, score: FACULTIES[key].keywords.filter((word) => haystack.includes(word)).length }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score) // stable: ties keep the SPECIFICITY order
    .map((entry) => entry.key);
}

const facultyHref = (key: FacultyKey) => `/faculty/0/${FACULTIES[key].slug}`;

const NEXT_STEPS: Record<Lang, string[]> = {
  uz: [
    "Fakultet sahifasi bilan tanishing",
    "my.edu.uz orqali onlayn roʻyxatdan oʻting va hujjatlarni yuklang (pasport, diplom, foto, tibbiy maʼlumotnoma)",
    "Savollar boʻlsa virtual qabulxonaga yozing yoki +998 95 062-23-45 raqamiga qoʻngʻiroq qiling",
  ],
  ru: [
    "Ознакомьтесь со страницей факультета",
    "Зарегистрируйтесь онлайн на my.edu.uz и загрузите документы (паспорт, диплом, фото, медицинская справка)",
    "Если есть вопросы — напишите в виртуальную приёмную или позвоните: +998 95 062-23-45",
  ],
  en: [
    "Read the faculty page",
    "Register online at my.edu.uz and upload your documents (passport, diploma, photo, medical certificate)",
    "If you have questions, write to the virtual reception or call +998 95 062-23-45",
  ],
};

export interface FacultyAdvice {
  faculty: string;
  why: string;
  alternatives: string[];
  next: string[];
  href: string;
}

export function staticFacultyAdvice(text: string, lang: string): FacultyAdvice {
  const l = toLang(lang);
  const ranked = rankFaculties(text);

  if (ranked.length === 0) {
    return {
      faculty: { uz: "Qiziqishingizni aniqroq yozing", ru: "Опишите интерес точнее", en: "Tell us a little more" }[l],
      why: {
        uz: "Yozganingizdan fakultetni aniq ajratib boʻlmadi. Qiziqishingizni 1–2 soʻz bilan yozing (masalan: bolalar, jarrohlik, epidemiologiya, xorijiy tillar) yoki toʻrt fakultetning har biri bilan tanishing.",
        ru: "По написанному не удалось определить факультет. Напишите интерес одним-двумя словами (например: дети, хирургия, эпидемиология, иностранные языки) или познакомьтесь с каждым из четырёх факультетов.",
        en: "We could not tell the faculty from what you wrote. Describe your interest in a word or two (for example: children, surgery, epidemiology, foreign languages) or look at each of the four faculties.",
      }[l],
      alternatives: FACULTY_ORDER.map((key) => FACULTIES[key].name[l]),
      next: [
        { uz: "PathFinder'da 3 qadamda yoʻnalish tanlang", ru: "Выберите направление в PathFinder за 3 шага", en: "Pick a direction in PathFinder in 3 steps" }[l],
        NEXT_STEPS[l][2],
      ],
      href: "/#faculties-news",
    };
  }

  const best = FACULTIES[ranked[0]];
  const alternativeKeys = [...ranked.slice(1), ...best.related.filter((key) => !ranked.includes(key))].slice(0, 2);
  return {
    faculty: best.name[l],
    why: {
      uz: `Yozganingiz boʻyicha «${best.name.uz}» mos keladi: u ${best.about.uz}.`,
      ru: `По вашему описанию подходит факультет «${best.name.ru}»: он ${best.about.ru}.`,
      en: `From what you wrote, “${best.name.en}” fits: it ${best.about.en}.`,
    }[l],
    alternatives: alternativeKeys.map((key) => FACULTIES[key].name[l]),
    next: NEXT_STEPS[l],
    href: facultyHref(ranked[0]),
  };
}

// --- PathFinder from free text -----------------------------------------------------------------

const LEVELS: Record<LevelKey, { name: L10n; about: L10n; keywords: string[] }> = {
  bakalavriat: {
    name: { uz: "Bakalavriat", ru: "Бакалавриат", en: "Bachelor's" },
    about: {
      uz: "oliy taʼlimning birinchi bosqichi, tibbiyot yoʻnalishida chuqur tayyorgarlik (taxminan 5 yil)",
      ru: "первая ступень высшего образования, углублённая подготовка по медицине (около 5 лет)",
      en: "the first stage of higher education, in-depth medical training (about 5 years)",
    },
    keywords: ["bakalavr", "бакалавр", "bachelor", "undergraduate"],
  },
  magistratura: {
    name: { uz: "Magistratura", ru: "Магистратура", en: "Master's" },
    about: {
      uz: "ilmiy-pedagogik ixtisoslashuv",
      ru: "научно-педагогическая специализация",
      en: "scientific and teaching specialisation",
    },
    keywords: ["magistr", "магистр", "master"],
  },
  ordinatura: {
    name: { uz: "Klinik ordinatura", ru: "Клиническая ординатура", en: "Clinical residency" },
    about: {
      uz: "shifokorlar uchun kasbiy qayta tayyorlash va malaka oshirish",
      ru: "профессиональная переподготовка и повышение квалификации для врачей",
      en: "professional retraining and further qualification for doctors",
    },
    keywords: ["ordinatur", "ординатур", "residen"],
  },
  doktorantura: {
    name: { uz: "Doktorantura", ru: "Докторантура", en: "Doctoral studies" },
    about: { uz: "ilmiy tadqiqot yoʻnalishi", ru: "научно-исследовательское направление", en: "the research track" },
    keywords: ["doktorant", "докторант", "doctoral", "phd"],
  },
};

const INTEREST_FACULTY: Record<string, FacultyKey | undefined> = { clinic: "davolash", public: "profilaktika", global: "xalqaro", science: undefined };

function detectLevel(text: string, chosen?: string): LevelKey | undefined {
  if (chosen && chosen in LEVELS) return chosen as LevelKey;
  const haystack = normalize(text);
  return (Object.keys(LEVELS) as LevelKey[]).find((key) => LEVELS[key].keywords.some((word) => haystack.includes(word)));
}

export interface PathfinderAdvice {
  title: string;
  summary: string;
  faculty?: string;
  level?: string;
  steps: string[];
  links: { label: string; href: string }[];
}

export function staticPathfinderAdvice(input: { freeText?: string; interest?: string; level?: string; lang: string }): PathfinderAdvice {
  const l = toLang(input.lang);
  const text = input.freeText || "";
  const ranked = rankFaculties(text);
  const interestFaculty = input.interest ? INTEREST_FACULTY[input.interest] : undefined;
  const facultyKey = ranked[0] ?? interestFaculty;
  const level = detectLevel(text, input.level);
  const science = input.interest === "science" || /ilmiy|tadqiqot|fan |научн|исследов|research|science/.test(normalize(text));

  const faculty = facultyKey ? FACULTIES[facultyKey] : undefined;
  const levelInfo = level ? LEVELS[level] : undefined;

  const summaryParts: string[] = [];
  if (faculty) {
    summaryParts.push(
      {
        uz: `Qiziqishingiz uchun «${faculty.name.uz}» mos keladi: u ${faculty.about.uz}.`,
        ru: `Для вашего интереса подходит факультет «${faculty.name.ru}»: он ${faculty.about.ru}.`,
        en: `For your interest “${faculty.name.en}” fits: it ${faculty.about.en}.`,
      }[l],
    );
  } else if (science) {
    summaryParts.push(
      {
        uz: "Ilmiy tadqiqot yoʻnalishi: kafedralar ilmiy ishni taʼlim va klinik amaliyot bilan birlashtiradi.",
        ru: "Научное направление: кафедры объединяют научную работу с обучением и клинической практикой.",
        en: "Research track: the departments combine research with teaching and clinical practice.",
      }[l],
    );
  } else {
    summaryParts.push(
      {
        uz: "Yozganingizdan fakultetni aniq ajratib boʻlmadi — toʻrt fakultetning har biri bilan tanishib, qiziqishingizga mosini tanlang.",
        ru: "По написанному не удалось определить факультет — познакомьтесь с каждым из четырёх факультетов и выберите подходящий.",
        en: "We could not tell the faculty from what you wrote — look at each of the four faculties and pick the one that fits.",
      }[l],
    );
  }
  if (levelInfo) {
    summaryParts.push(
      {
        uz: `${levelInfo.name.uz} — ${levelInfo.about.uz}.`,
        ru: `${levelInfo.name.ru} — ${levelInfo.about.ru}.`,
        en: `${levelInfo.name.en} — ${levelInfo.about.en}.`,
      }[l],
    );
  }
  if (science) {
    summaryParts.push(
      {
        uz: "Ilmiy tadqiqotlar boʻyicha yoʻnalishlar va doktorantura haqida pastdagi havolalarda yozilgan.",
        ru: "О научных направлениях и докторантуре — по ссылкам ниже.",
        en: "Research directions and doctoral studies are described at the links below.",
      }[l],
    );
  }

  const links: { label: string; href: string }[] = [];
  if (facultyKey) links.push({ label: { uz: "Fakultet sahifasi", ru: "Страница факультета", en: "Faculty page" }[l], href: facultyHref(facultyKey) });
  if (science) {
    links.push({ label: { uz: "Ilmiy tadqiqot yoʻnalishlari", ru: "Научные направления", en: "Research directions" }[l], href: "/blog/1993/ilmiy-tadqiqot-yonalishlari" });
    links.push({ label: { uz: "Doktorantura", ru: "Докторантура", en: "Doctoral studies" }[l], href: "/blog/2042/doktorantura-malumotlari" });
  }
  links.push({ label: { uz: "Virtual qabulxona", ru: "Виртуальная приёмная", en: "Virtual reception" }[l], href: "/virtual-reception/17" });

  return {
    title: faculty
      ? { uz: `Sizga mos yoʻnalish: ${faculty.name.uz}`, ru: `Вам подходит: ${faculty.name.ru}`, en: `A good fit: ${faculty.name.en}` }[l]
      : science
        ? { uz: "Ilmiy tadqiqot yoʻnalishi", ru: "Научное направление", en: "Research track" }[l]
        : { uz: "Yoʻnalishni birgalikda aniqlaymiz", ru: "Определим направление вместе", en: "Let's find the direction together" }[l],
    summary: summaryParts.join(" "),
    faculty: faculty?.name[l],
    level: levelInfo?.name[l],
    steps: faculty
      ? NEXT_STEPS[l]
      : [
          science
            ? { uz: "Ilmiy yoʻnalishlar va doktorantura sahifalari bilan tanishing", ru: "Изучите страницы о научных направлениях и докторантуре", en: "Read the pages on research directions and doctoral studies" }[l]
            : { uz: "Bosh sahifadagi fakultetlar boʻlimida toʻrt fakultet bilan tanishing", ru: "Познакомьтесь с четырьмя факультетами в разделе факультетов на главной странице", en: "Look at the four faculties in the faculties section of the home page" }[l],
          ...NEXT_STEPS[l].slice(1),
        ],
    links,
  };
}
