export interface TestResultPdfQuestion {
  number: number;
  question: string;
  selectedOption?: string;
  correctOption: string;
  explanation?: string;
  isCorrect: boolean;
}

export interface TestResultPdfLabels {
  title: string;
  subject: string;
  result: string;
  correctAnswers: string;
  score: string;
  yourAnswer: string;
  correctAnswer: string;
  explanation: string;
  correct: string;
  incorrect: string;
  notAnswered: string;
  page: string;
}

interface DownloadTestResultPdfParams {
  subjectName: string;
  score: number;
  total: number;
  percent: number;
  questions: TestResultPdfQuestion[];
  labels: TestResultPdfLabels;
  locale: string;
}

type PdfMake = {
  addVirtualFileSystem: (files: unknown) => void;
  createPdf: (definition: unknown) => { download: (filename: string) => void };
};

/**
 * The font bundled with pdfmake (Roboto) has no glyph for the Uzbek letter mark o\u02bb g\u02bb (U+02BB): each one
 * came out as an empty box and the neighbouring words ran together ("To\u25a1 g\u25a1 ri", "so\u25a1 ngmakrofaglar"). The
 * left single quotation mark o\u2018 g\u2018 (U+2018) is in that font and looks the same, so the PDF uses it.
 */
export function pdfText(text: string): string {
  return text.replace(/\u02bb/g, "\u2018");
}

/** dd.mm.yyyy: the browser's own "medium" format came out as "2026 M11 14" for the Uzbek locale. */
export function pdfDate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear()}`;
}

export function buildTestResultPdfDefinition({ subjectName, score, total, percent, questions, labels }: DownloadTestResultPdfParams, now = new Date()) {
  const L = Object.fromEntries(Object.entries(labels).map(([key, value]) => [key, pdfText(value)])) as unknown as TestResultPdfLabels;
  const generatedAt = pdfDate(now);

  const questionBlock = (item: TestResultPdfQuestion) => [
    {
      // the question and its answer table stay together on one page ...
      unbreakable: true,
      stack: [
        { text: pdfText(`${item.number}. ${item.question}`), style: "question", color: item.isCorrect ? "#172033" : "#b42318" },
        {
          table: {
            widths: [118, "*"],
            body: [
              [
                { text: L.yourAnswer, style: "label" },
                { text: pdfText(item.selectedOption || L.notAnswered), color: item.isCorrect ? "#157347" : "#b42318" },
              ],
              [{ text: L.correctAnswer, style: "label" }, { text: pdfText(item.correctOption), color: "#157347" }],
              [{ text: L.result, style: "label" }, { text: item.isCorrect ? L.correct : L.incorrect, color: item.isCorrect ? "#157347" : "#b42318" }],
            ],
          },
          layout: {
            hLineColor: () => "#d9e0ea",
            vLineColor: () => "#d9e0ea",
            paddingLeft: () => 7,
            paddingRight: () => 7,
            paddingTop: () => 5,
            paddingBottom: () => 5,
          },
        },
      ],
    },
    // ... but the explanation (long, often 20+ lines) may flow onto the next page: keeping the whole block unbreakable left
    // pages two thirds empty and turned 20 questions into 15 pages
    item.explanation
      ? { text: pdfText(`${L.explanation}: ${item.explanation}`), style: "explanation", margin: [0, 7, 0, 15] }
      : { text: "", margin: [0, 0, 0, 15] },
  ];

  return {
    pageSize: "A4",
    pageMargins: [44, 48, 44, 42],
    defaultStyle: { font: "Roboto", fontSize: 10, color: "#172033" },
    content: [
      { text: L.title, style: "title" },
      { text: `${L.subject}: ${pdfText(subjectName)}`, style: "subject" },
      {
        columns: [
          { text: `${L.correctAnswers}: ${score} / ${total}`, style: "summary" },
          { text: `${L.score}: ${percent}%`, style: "summary", alignment: "right" },
        ],
        margin: [0, 10, 0, 18],
      },
      ...questions.flatMap(questionBlock),
    ],
    styles: {
      title: { fontSize: 20, bold: true, color: "#163b72" },
      subject: { fontSize: 11, color: "#4d5b73", margin: [0, 5, 0, 0] },
      summary: { bold: true, fontSize: 11, color: "#163b72" },
      question: { bold: true, fontSize: 11, margin: [0, 0, 0, 7] },
      label: { bold: true, color: "#4d5b73" },
      explanation: { italics: true, color: "#4d5b73" },
    },
    footer: (currentPage: number) => ({
      text: `${L.page} ${currentPage} - ${generatedAt}`,
      alignment: "center",
      fontSize: 8,
      color: "#667085",
      margin: [0, 12, 0, 0],
    }),
  };
}

export async function downloadTestResultPdf(params: DownloadTestResultPdfParams) {
  const [{ default: pdfMake }, { default: pdfFonts }] = await Promise.all([
    import("pdfmake/build/pdfmake.js"),
    import("pdfmake/build/vfs_fonts.js"),
  ]);

  const pdf = pdfMake as PdfMake;
  pdf.addVirtualFileSystem(pdfFonts);

  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  pdf.createPdf(buildTestResultPdfDefinition(params, now)).download(`test-natija-${date}.pdf`);
}
