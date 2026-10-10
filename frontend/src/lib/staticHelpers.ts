/**
 * Static (no AI service) helpers for three small panels: the admission question box on /qabul, the "prepare my
 * message" box on the virtual reception form and the suggestions above the search results. They work without the
 * OpenAI proxy, so the panels never answer "temporarily unavailable"; when the AI service is switched on, these
 * are also what a failed AI call falls back to.
 *
 * Only facts the site already states are used (admission steps, study levels, call-centre number, page list).
 * Nothing is invented: dates, prices and quotas are NOT on the site, so a question about them is answered by
 * pointing to my.edu.uz and the call centre.
 */
import { HEMIS_URL } from "@/lib/externalLinks";
import { toLang } from "@/lib/staticAdvisor";

type Lang = "uz" | "ru" | "en";
type L10n = Record<Lang, string>;
export interface StaticLink {
  label: string;
  href: string;
}

const PHONE = "+998 95 062-23-45";

/** lower case, apostrophe variants removed, so "o'qish" / "oʻqish" / "oqish" all look alike */
function norm(s: string) {
  return String(s || "")
    .toLowerCase()
    .replace(/[ʻʼ’'`‘]/g, "")
    .replace(/ё/g, "е");
}

function hasAny(text: string, stems: string[]) {
  return stems.some((s) => text.includes(s));
}

// ---------------------------------------------------------------- admission

interface QabulTopic {
  stems: string[];
  reply: L10n;
}

const QABUL_LINKS: Record<Lang, StaticLink[]> = {
  uz: [
    { label: "Qabul sahifasi", href: "/qabul" },
    { label: "my.edu.uz", href: "https://my.edu.uz" },
    { label: "Virtual qabulxona", href: "/virtual-qabulxona" },
  ],
  ru: [
    { label: "Страница приёма", href: "/qabul" },
    { label: "my.edu.uz", href: "https://my.edu.uz" },
    { label: "Виртуальная приёмная", href: "/virtual-qabulxona" },
  ],
  en: [
    { label: "Admission page", href: "/qabul" },
    { label: "my.edu.uz", href: "https://my.edu.uz" },
    { label: "Virtual reception", href: "/virtual-qabulxona" },
  ],
};

const QABUL_STEPS: L10n = {
  uz: `Qabul 4 bosqichda oʻtadi:\n1. my.edu.uz saytida onlayn roʻyxatdan oʻting\n2. Hujjatlarni yuklang: pasport, diplom, fotosurat, tibbiy maʻlumotnoma\n3. Belgilangan sanada test sinovlarida ishtirok eting\n4. Natijani koʻrib, institutda roʻyxatdan oʻting\n\nAniq savol boʻlsa, call-markaz: ${PHONE}.`,
  ru: `Приём проходит в 4 этапа:\n1. Зарегистрируйтесь онлайн на my.edu.uz\n2. Загрузите документы: паспорт, диплом, фото, медицинская справка\n3. Пройдите тесты в назначенную дату\n4. Узнайте результат и зарегистрируйтесь в институте\n\nЕсли нужен точный ответ, звоните в колл-центр: ${PHONE}.`,
  en: `Admission has 4 steps:\n1. Register online at my.edu.uz\n2. Upload your documents: passport, diploma, photo, medical certificate\n3. Take the entrance tests on the set date\n4. See the result and register at the institute\n\nFor a precise answer call the call centre: ${PHONE}.`,
};

const QABUL_TOPICS: QabulTopic[] = [
  {
    // dates, prices, quotas: the site does not state them
    stems: [
      "muddat", "qachon", "sana", "oxirgi kun", "deadline", "when", "date", "срок", "когда", "дата",
      "narx", "kontrakt", "tolov", "price", "cost", "fee", "contract", "tuition", "стоимост", "контракт", "цена", "оплат",
      "kvota", "oʻrin", "orin soni", "grant", "quota", "places", "квот", "мест",
    ],
    reply: {
      uz: `Qabul sanalari, kontrakt narxi va oʻrinlar soni har yili e'lon qilinadi, shuning uchun bu sahifada eskirgan raqam koʻrsatmaymiz. Joriy maʻlumotni my.edu.uz saytidan yoki call-markazdan (${PHONE}) oling.`,
      ru: `Даты приёма, стоимость контракта и количество мест объявляются каждый год, поэтому мы не показываем здесь устаревшие цифры. Актуальные данные — на my.edu.uz или в колл-центре (${PHONE}).`,
      en: `Admission dates, contract fees and the number of places are announced every year, so we do not show possibly outdated numbers here. Get the current figures on my.edu.uz or from the call centre (${PHONE}).`,
    },
  },
  {
    stems: ["hujjat", "document", "документ", "pasport", "passport", "паспорт", "diplom", "диплом", "spravka", "маʼлумотнома", "malumotnoma", "справк", "certificate"],
    reply: {
      uz: "Qabul uchun hujjatlar: pasport, diplom, fotosurat va tibbiy maʻlumotnoma. Ularni my.edu.uz saytidagi shaxsiy kabinetingiz orqali yuklaysiz. Qoʻshimcha hujjat talab etilsa, u my.edu.uz da koʻrsatiladi.",
      ru: "Документы для поступления: паспорт, диплом, фотография и медицинская справка. Их загружают в личном кабинете на my.edu.uz. Если потребуются дополнительные документы, это будет указано на my.edu.uz.",
      en: "Documents for admission: passport, diploma, photo and a medical certificate. You upload them in your personal account on my.edu.uz. If anything else is required it is shown on my.edu.uz.",
    },
  },
  {
    stems: ["ordinatur", "ординатур", "residen"],
    reply: {
      uz: "Klinik ordinatura — shifokorlarni kasbiy qayta tayyorlash va malakasini oshirish tizimi. Ariza va hujjatlar umumiy qabul tartibida, my.edu.uz orqali topshiriladi.",
      ru: "Клиническая ординатура — система профессиональной переподготовки и повышения квалификации врачей. Заявление и документы подаются в общем порядке приёма, через my.edu.uz.",
      en: "Clinical residency (ordinatura) is the system for professional retraining and upskilling of doctors. The application and documents go through the general admission procedure on my.edu.uz.",
    },
  },
  {
    stems: ["magistr", "магистр", "master"],
    reply: {
      uz: "Magistratura — ilmiy va pedagogik faoliyatga ixtisoslashish uchun ikkinchi bosqich taʻlim. Ariza my.edu.uz orqali topshiriladi.",
      ru: "Магистратура — вторая ступень образования для специализации в научной и педагогической деятельности. Заявление подаётся через my.edu.uz.",
      en: "The master's programme is the second level of study, specialising in research and teaching. You apply through my.edu.uz.",
    },
  },
  {
    stems: ["bakalavr", "бакалавр", "bachelor", "undergrad"],
    reply: {
      uz: "Bakalavriat — oliy taʻlimning birinchi bosqichi; tibbiyot sohasida taxminan 5 yillik taʻlim. Ariza my.edu.uz orqali topshiriladi.",
      ru: "Бакалавриат — первая ступень высшего образования; в медицине около 5 лет обучения. Заявление подаётся через my.edu.uz.",
      en: "The bachelor's programme is the first level of higher education; about 5 years in medicine. You apply through my.edu.uz.",
    },
  },
  {
    stems: ["doktorantur", "докторантур", "doctoral", "phd"],
    reply: {
      uz: "Doktorantura — ilmiy tadqiqot yoʻnalishi. Qabul shartlarini /qabul sahifasidan yoki call-markazdan aniqlang.",
      ru: "Докторантура — направление научных исследований. Условия приёма уточняйте на странице /qabul или в колл-центре.",
      en: "The doctoral programme is the research track. Check the entry conditions on the /qabul page or with the call centre.",
    },
  },
  {
    stems: ["test", "imtihon", "sinov", "exam", "тест", "экзамен", "испытан"],
    reply: {
      uz: "Test sinovlari — qabulning 3-bosqichi, belgilangan sanada oʻtkaziladi. Sana va joyni my.edu.uz da koʻring. Tayyorlanish uchun saytdagi «Test» boʻlimida mashq qilishingiz mumkin.",
      ru: "Тесты — 3-й этап приёма, проводятся в назначенную дату. Дату и место смотрите на my.edu.uz. Для подготовки можно потренироваться в разделе «Тест» на сайте.",
      en: "The tests are step 3 of admission and take place on a set date. See the date and place on my.edu.uz. To prepare, you can practise in the site's “Test” section.",
    },
  },
  {
    stems: ["natija", "result", "результат", "mandat", "ball", "балл"],
    reply: {
      uz: "Natijalar «Qabul natijalari» sahifasida va my.edu.uz dagi shaxsiy kabinetda koʻrinadi. Keyin institutda roʻyxatdan oʻtasiz.",
      ru: "Результаты видны на странице «Результаты приёма» и в личном кабинете на my.edu.uz. После этого вы регистрируетесь в институте.",
      en: "Results appear on the “Admission results” page and in your account on my.edu.uz. After that you register at the institute.",
    },
  },
  {
    stems: ["royxat", "ariza", "qanday topshir", "qanday kir", "register", "apply", "how to", "регистр", "заявлен", "как поступ", "как подат"],
    reply: {
      uz: "Ariza topshirish uchun my.edu.uz saytida onlayn roʻyxatdan oʻting va maʻlumotlaringizni toʻldiring, soʻng hujjatlarni yuklang.",
      ru: "Чтобы подать заявление, зарегистрируйтесь на my.edu.uz, заполните данные и загрузите документы.",
      en: "To apply, register on my.edu.uz, fill in your details and upload the documents.",
    },
  },
];

/** answer to an admission question; the 4 admission steps when no topic is recognised */
export function staticQabulAnswer(question: string, lang: string): { reply: string; links: StaticLink[] } {
  const l = toLang(lang);
  const text = norm(question);
  const topic = QABUL_TOPICS.find((tp) => hasAny(text, tp.stems.map(norm)));
  const reply = topic ? topic.reply[l] : QABUL_STEPS[l];
  const links = [...QABUL_LINKS[l]];
  if (topic?.stems.includes("natija")) {
    links.unshift({ label: l === "uz" ? "Qabul natijalari" : l === "ru" ? "Результаты приёма" : "Admission results", href: "/qabul-natijalari" });
  }
  return { reply, links };
}

// ---------------------------------------------------- virtual reception text

const RECEPTION_CATEGORIES: { stems: string[]; label: L10n }[] = [
  { stems: ["shikoyat", "norozi", "жалоб", "complain"], label: { uz: "Shikoyat", ru: "Жалоба", en: "Complaint" } },
  { stems: ["taklif", "fikr", "предложен", "suggest", "idea"], label: { uz: "Taklif", ru: "Предложение", en: "Suggestion" } },
  { stems: ["qabul", "abituriyent", "ariza", "поступл", "приём", "прием", "admission", "apply"], label: { uz: "Qabul", ru: "Приём", en: "Admission" } },
  { stems: ["stipendiya", "kontrakt", "tolov", "стипенд", "контракт", "оплат", "tuition", "scholarship"], label: { uz: "Stipendiya va toʻlov", ru: "Стипендия и оплата", en: "Scholarship and fees" } },
  { stems: ["maʼlumotnoma", "malumotnoma", "diplom", "hujjat", "справк", "диплом", "документ", "certificate", "document"], label: { uz: "Hujjat va maʻlumotnoma", ru: "Документы и справки", en: "Documents" } },
  { stems: ["dars", "oqituvchi", "jadval", "imtihon", "baho", "урок", "расписан", "оценк", "преподав", "exam", "grade", "schedule"], label: { uz: "Oʻquv jarayoni", ru: "Учебный процесс", en: "Studies" } },
  { stems: ["yotoqxona", "ovqat", "общежит", "dormitor", "hostel"], label: { uz: "Yotoqxona va xizmatlar", ru: "Общежитие и услуги", en: "Dormitory and services" } },
];

const FALLBACK_SUBJECT: L10n = { uz: "Murojaat", ru: "Обращение", en: "Enquiry" };

function firstSentences(text: string, maxChars: number, maxSentences: number) {
  const sentences = text.match(/[^.!?]+[.!?]*/g)?.map((s) => s.trim()).filter(Boolean) ?? [text];
  let out = "";
  let n = 0;
  for (const s of sentences) {
    if (n >= maxSentences || (out && (out + " " + s).length > maxChars)) break;
    out = out ? out + " " + s : s;
    n++;
  }
  if (out.length > maxChars) out = out.slice(0, maxChars - 1).replace(/\s+\S*$/, "") + "…";
  return out;
}

/**
 * "Tidy" a message without changing its meaning: collapses spaces and blank lines, capitalises sentence starts,
 * repeats of "!!!"/"???" and a missing final full stop. The subject is the first sentence, the category is picked
 * by keywords, the short summary is the first one or two sentences.
 */
export function staticReceptionHelp(text: string, lang: string) {
  const l = toLang(lang);
  const cleaned = String(text || "")
    .replace(/\r/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/ ?\n ?/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/([!?.,])\1{1,}/g, "$1")
    .replace(/\s+([,.;:!?])/g, "$1")
    .replace(/([,;])(?=[^\s\d])/gu, "$1 ")
    .trim();
  const polished = cleaned
    .replace(/(^|[.!?]\s+|\n)(\p{Ll})/gu, (_m, pre: string, ch: string) => pre + ch.toUpperCase())
    .replace(/(^|\s)i(?=\s|')/g, l === "en" ? "$1I" : "$&")
    .replace(/([^.!?:;])$/u, "$1.");

  const lowered = norm(cleaned);
  const category = RECEPTION_CATEGORIES.find((c) => hasAny(lowered, c.stems.map(norm)))?.label[l] ?? "";
  // a short greeting ("Salom, hurmatli rektor!") makes a poor subject: take the first sentence with real content
  const sentences = polished.match(/[^.!?]+[.!?]*/g)?.map((x) => x.trim()).filter(Boolean) ?? [];
  const lead = sentences.find((x) => x.split(/\s+/).length >= 4) ?? sentences[0] ?? "";
  const subject = firstSentences(lead, 80, 1).replace(/[.!?…]+$/u, "") || FALLBACK_SUBJECT[l];
  const summary = firstSentences(polished, 220, 2);
  return { polished, subject, category, summary };
}

// ------------------------------------------------------------------- search

interface SitePage {
  href: string;
  stems: string[];
  title: L10n;
  reason: L10n;
}

const SITE_PAGES: SitePage[] = [
  {
    href: "/qabul",
    stems: ["qabul", "abituriyent", "ariza", "hujjat", "ordinatur", "magistr", "bakalavr", "поступл", "приём", "прием", "admission", "apply", "enrol"],
    title: { uz: "Qabul", ru: "Приём", en: "Admission" },
    reason: { uz: "Qabul bosqichlari, hujjatlar va ariza", ru: "Этапы приёма, документы и заявление", en: "Admission steps, documents and application" },
  },
  {
    href: "/qabul-natijalari",
    stems: ["natija", "mandat", "result", "результат"],
    title: { uz: "Qabul natijalari", ru: "Результаты приёма", en: "Admission results" },
    reason: { uz: "Qabul natijalarini koʻrish", ru: "Просмотр результатов приёма", en: "See the admission results" },
  },
  {
    href: "/#faculties-news",
    stems: ["fakultet", "факультет", "faculty", "faculties", "davolash", "pediatri", "profilaktika", "xalqaro", "лечебн", "педиатр", "профилакт", "international"],
    title: { uz: "Fakultetlar", ru: "Факультеты", en: "Faculties" },
    reason: { uz: "Institutning fakultetlari va ularni tanlash", ru: "Факультеты института и выбор факультета", en: "The institute's faculties and how to choose" },
  },
  {
    href: "/test",
    stems: ["test", "тест", "mashq", "tayyorgarlik", "syllabus", "fan"],
    title: { uz: "Test", ru: "Тест", en: "Tests" },
    reason: { uz: "Fanlar boʻyicha testlar va oʻzingizni sinab koʻrish", ru: "Тесты по предметам и самопроверка", en: "Subject tests and the self-check quiz" },
  },
  {
    href: "/keyslar",
    stems: ["keys", "кейс", "case", "klinik"],
    title: { uz: "Keyslar", ru: "Кейсы", en: "Cases" },
    reason: { uz: "Klinik keyslar katalogi", ru: "Каталог клинических кейсов", en: "Clinical case catalogue" },
  },
  {
    href: "/schedule",
    stems: ["jadval", "dars", "schedule", "расписан", "timetable"],
    title: { uz: "Dars jadvali", ru: "Расписание", en: "Schedule" },
    reason: { uz: "Dars jadvallari", ru: "Расписание занятий", en: "Class timetables" },
  },
  {
    href: HEMIS_URL,
    stems: ["hemis", "хемис", "baho", "kabinet", "оценк", "кабинет", "grade"],
    title: { uz: "HEMIS", ru: "HEMIS", en: "HEMIS" },
    reason: { uz: "Talaba shaxsiy kabineti, baholar, jadval", ru: "Личный кабинет студента, оценки, расписание", en: "Student account, grades, schedule" },
  },
  {
    href: "/yangiliklar",
    stems: ["yangilik", "xabar", "tadbir", "новост", "событи", "news", "event"],
    title: { uz: "Yangiliklar", ru: "Новости", en: "News" },
    reason: { uz: "Institut yangiliklari va tadbirlari", ru: "Новости и мероприятия института", en: "Institute news and events" },
  },
  {
    href: "/galereya",
    stems: ["rasm", "foto", "galere", "photo", "gallery", "фото", "галере"],
    title: { uz: "Galereya", ru: "Галерея", en: "Gallery" },
    reason: { uz: "Foto va albomlar", ru: "Фото и альбомы", en: "Photos and albums" },
  },
  {
    href: "/video",
    stems: ["video", "видео"],
    title: { uz: "Video", ru: "Видео", en: "Video" },
    reason: { uz: "Video materiallar", ru: "Видеоматериалы", en: "Video material" },
  },
  {
    href: "/aloqa",
    stems: ["aloqa", "telefon", "manzil", "email", "pochta", "контакт", "телефон", "адрес", "contact", "phone", "address"],
    title: { uz: "Aloqa", ru: "Контакты", en: "Contact" },
    reason: { uz: "Manzil, telefon va xarita", ru: "Адрес, телефон и карта", en: "Address, phone and map" },
  },
  {
    href: "/virtual-qabulxona",
    stems: ["murojaat", "shikoyat", "taklif", "rektor", "qabulxona", "обращен", "жалоб", "приёмная", "приемная", "complain", "reception"],
    title: { uz: "Virtual qabulxona", ru: "Виртуальная приёмная", en: "Virtual reception" },
    reason: { uz: "Rahbariyatga rasmiy murojaat", ru: "Официальное обращение к руководству", en: "Official appeal to the leadership" },
  },
  {
    href: "/sitemap",
    stems: ["sayt xaritasi", "xarita", "sitemap", "карта сайта"],
    title: { uz: "Sayt xaritasi", ru: "Карта сайта", en: "Sitemap" },
    reason: { uz: "Saytning barcha boʻlimlari", ru: "Все разделы сайта", en: "All sections of the site" },
  },
];

const SEARCH_INTRO: Record<Lang, { found: (q: string) => string; none: (q: string) => string }> = {
  uz: {
    found: (q) => `«${q}» boʻyicha natijalardan tashqari, mos boʻlimlar:`,
    none: (q) => `«${q}» uchun alohida boʻlim topilmadi. Quyidagi natijalarni koʻring yoki boshqa soʻz bilan yozing.`,
  },
  ru: {
    found: (q) => `Кроме результатов по запросу «${q}», подходящие разделы:`,
    none: (q) => `Отдельного раздела по запросу «${q}» не найдено. Посмотрите результаты ниже или попробуйте другие слова.`,
  },
  en: {
    found: (q) => `Besides the results for “${q}”, these sections may help:`,
    none: (q) => `No dedicated section matches “${q}”. See the results below or try other words.`,
  },
};

/** up to 4 site sections whose keywords appear in the query; none → the panel stays hidden */
export function staticSearchHints(query: string, lang: string) {
  const l = toLang(lang);
  const q = norm(query);
  const suggestions = SITE_PAGES.filter((p) => hasAny(q, p.stems.map(norm)))
    .slice(0, 4)
    .map((p) => ({ title: p.title[l], href: p.href, reason: p.reason[l] }));
  const short = query.trim().slice(0, 60);
  return {
    interpretation: suggestions.length ? SEARCH_INTRO[l].found(short) : SEARCH_INTRO[l].none(short),
    suggestions,
  };
}
