const abbreviations = /^(?:AKT|IT|AI|OAV|FJSTI|OTM|OʻR|O‘R|O’R|O'R|МЗ|СМИ|ИТ|РФ|[IVXLCDM]+)$/u;

export function normalizeTechnicalCollegeHeading(text: string): string {
  if (text !== text.toUpperCase() || !/\p{Lu}/u.test(text)) return text;

  let firstWord = true;
  return text.replace(/[\p{L}]+(?:[ʻʼ‘’'][\p{L}]+)*/gu, (word) => {
    const capitalize = firstWord;
    firstWord = false;
    if (abbreviations.test(word)) return word;
    return capitalize ? word[0] + word.slice(1).toLowerCase() : word.toLowerCase();
  });
}

export function repairTechnicalCollegeText(text: string): string {
  return text
      .replace(/MA\s*['‘’ʻ]\s*NAVI\s*Y\s*-\s*MA\s*['‘’ʻ]\s*R\s*IFIY ISHLARI/gu, "Ma’naviy-ma’rifiy ishlar")
      .replace(/O\s*['‘’ʻʼ]\s*Q\s*U\s*V\s+VA\s+O\s*['‘’ʻʼ]\s*Q\s*U\s*V\s*[-–—]\s*METODIK\s+ISHLARI?\b/gu, "O‘quv va o‘quv-metodik ishlar")
      .replace(/O[‘’ʻ']\s*q\s*itis\s*h\s*ar bir/gu, "O‘qitish har bir")
      .replace(
        /O[‘’ʻ']\s*q\s*itis\s*h\s*j\s*a\s*ray\s*o\s*n\s*i\s*d\s*a\s*q\s*u\s*y\s*i\s*dag\s*i\s*t\s*ex\s*n\s*ik\s*ta[‘’ʻ']minotlar mavjud/gu,
        "O‘qitish jarayonida quyidagi texnik ta’minotlar mavjud",
      );
}

export function normalizeTechnicalCollegeHtml(html: string): string {
  if (typeof DOMParser === "undefined") return html;
  const { body } = new DOMParser().parseFromString(html, "text/html");
  let changed = false;
  for (const heading of body.querySelectorAll("h1, h2, h3, h4, h5, h6")) {
    const walker = heading.ownerDocument.createTreeWalker(heading, NodeFilter.SHOW_TEXT);
    const nodes: Text[] = [];
    while (walker.nextNode()) nodes.push(walker.currentNode as Text);
    const original = nodes.map((node) => node.data).join("");
    const normalized = normalizeTechnicalCollegeHeading(repairTechnicalCollegeText(original));
    if (normalized === original) continue;
    if (nodes.length === 1) {
      nodes[0].data = normalized;
    } else if (normalized.length === original.length) {
      let offset = 0;
      for (const node of nodes) {
        const end = offset + node.length;
        node.data = normalized.slice(offset, end);
        offset = end;
      }
    } else continue;
    changed = true;
  }
  return changed ? body.innerHTML : html;
}
