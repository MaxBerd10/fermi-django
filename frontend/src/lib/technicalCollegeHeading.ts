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
