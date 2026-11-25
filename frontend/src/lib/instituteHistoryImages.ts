const HISTORY_IMAGES = [
  [/mirza[ye]+v/i, "mirzayev"],
  [/nishano|nishonov/i, "nishonov"],
  [/mamatqulov/i, "mamatqulov"],
  [/usmanov/i, "usmanov"],
  [/sultanov/i, "sultanov"],
  [/abdur[ahx]+monov/i, "abduraxmonov"],
  [/[kq]orab[ao][ye]+v/i, "koraboyev"],
  [/rasulov(?![a-z])/i, "rasulov"],
  [/sidikov/i, "sidikov"],
  [/is[ao][kq]ov|isoqov/i, "isakov"],
  [/botirov/i, "botirov"],
  [/normatova/i, "normatova"],
  [/boltab[ao][ye]+v/i, "boltaboyev"],
  [/qodirova|munira[\s_-]+rasulovna/i, "qodirova"],
  [/screenshot[_-]1(?:[_.-]|$)/i, "archive"],
  // The same people are written in Cyrillic in the Russian text, so the Russian page finds the same portraits.
  [/мирзае?в/i, "mirzayev"],
  [/нишонов/i, "nishonov"],
  [/маматкулов/i, "mamatqulov"],
  [/усманов/i, "usmanov"],
  [/султанов/i, "sultanov"],
  [/абдурахмонов/i, "abduraxmonov"],
  [/кораб[оа]ев/i, "koraboyev"],
  [/расулов(?![а-яё])/i, "rasulov"],
  [/сидиков/i, "sidikov"],
  [/исаков|исоков/i, "isakov"],
  [/ботиров/i, "botirov"],
  [/норматова/i, "normatova"],
  [/болтабо[её]в/i, "boltaboyev"],
  [/кодирова|мунира\s+расуловна/i, "qodirova"],
] as const;

/** Match official filenames, including the suffix added during Django media migration. */
export function localInstituteHistoryImage(src: string): string | undefined {
  const path = src.split(/[?#]/, 1)[0];
  const filename = path.slice(path.lastIndexOf("/") + 1).replace(/%20/gi, " ");
  const match = HISTORY_IMAGES.find(([pattern]) => pattern.test(filename));
  return match && `/images/institute-history/${match[1]}.webp`;
}
