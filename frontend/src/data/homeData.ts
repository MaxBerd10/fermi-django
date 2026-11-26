import { HEMIS_URL } from "@/lib/externalLinks";

// The two lists the live site still takes from here: the menu used before the API answers, and the links of the partners strip.
// (The rest of this file belonged to the old home-page prototype and was removed with it.)
export const partners = [
  { name: "Prezident portali", icon: "ri-government-line", href: "https://president.uz/uz" },
  { name: "Qonun hujjatlari maʻlumotlar bazasi", icon: "ri-file-list-line", href: "https://lex.uz/" },
  { name: "Hukumat portali", icon: "ri-building-line", href: "https://gov.uz/uz" },
  { name: "Vazirlik (OTMFI)", icon: "ri-graduation-cap-line", href: "https://gov.uz/en/edu" },
  { name: "SSV", icon: "ri-heart-pulse-line", href: "https://ssv.uz/uz" },
  { name: "Study in Uzbekistan", icon: "ri-global-line", href: "https://studyin-uzbekistan.uz/universities/80" },
  { name: "Korrupsiyaga qarshi", icon: "ri-shield-check-line", href: "/about/korrupsiyaga-qarshi-kurashish-davlat-dasturlari" },
  { name: "HEMIS", icon: "ri-database-2-line", href: HEMIS_URL },
];

export const navItems = [
  {
    label: "Institut",
    href: "/institut",
    children: [
      { label: "Institut haqida", href: "/institut" },
      { label: "Missiya va tarix", href: "/institut#tarix" },
      { label: "Rahbariyat", href: "/institut/rahbariyat" },
      { label: "Tuzilma", href: "/institut/tuzilma" },
      { label: "Sertifikatlar", href: "/institut#sertifikatlar" },
      { label: "Xalqaro akkreditatsiya", href: "/institut#akkreditatsiya" },
      { label: "Institut binolari", href: "/institut#binolar" },
      { label: "Ilmiy kengash", href: "/institut#ilmiy-kengash" },
    ],
  },
  {
    label: "Tuzilma",
    href: "/tuzilma",
    children: [
      { label: "Rahbariyat", href: "/institut/rahbariyat" },
      { label: "Fakultetlar", href: "/fakultetlar" },
      { label: "Kafedralar", href: "/kafedralar" },
      { label: "Boʻlimlar", href: "/tuzilma#bolimlar" },
      { label: "Markazlar", href: "/tuzilma#markazlar" },
      { label: "Texnikumlar", href: "/tuzilma#texnikumlar" },
      { label: "Karyera markazi", href: "/tuzilma#karyera" },
    ],
  },
  {
    label: "Faoliyat",
    href: "/faoliyat",
    children: [
      { label: "Ilmiy faoliyat", href: "/faoliyat/ilmiy" },
      { label: "Xalqaro faoliyat", href: "/faoliyat/xalqaro" },
      { label: "Moliyaviy faoliyat", href: "/faoliyat/moliyaviy" },
      { label: "Madaniy-maʻrifiy faʻoliyat", href: "/faoliyat/madaniy" },
      { label: "Korrupsiyaga qarshi kurashish", href: "/about/korrupsiyaga-qarshi-kurashish-davlat-dasturlari" },
      { label: "Loyihalar", href: "/faoliyat/loyihalar" },
      { label: "Doktorantura", href: "/faoliyat/doktorantura" },
    ],
  },
  {
    label: "Abiturient",
    href: "/qabul",
    children: [
      { label: "Bakalavriat", href: "/qabul/bakalavriat" },
      { label: "Magistratura", href: "/qabul/magistratura" },
      { label: "Ordinatura", href: "/qabul/ordinatura" },
      { label: "Qoʻshma taʻlim", href: "/qabul/qoshma" },
      { label: "Doktorantura", href: "/qabul/doktorantura" },
      { label: "Internatura", href: "/qabul/internatura" },
      { label: "Xorijiy fuqarolar", href: "/qabul/xorijiy" },
      { label: "Texnikum bitiruvchilari", href: "/qabul/texnikum" },
    ],
  },
  {
    label: "Talabalar",
    href: "/talabalar",
    children: [
      { label: "Bakalavriat", href: "/talabalar/bakalavriat" },
      { label: "Magistratura", href: "/talabalar/magistratura" },
      { label: "Ordinatura", href: "/talabalar/ordinatura" },
      { label: "Xalqaro talabalar", href: "/talabalar/xalqaro" },
      { label: "Iqtidorli talabalar", href: "/talabalar/iqtidorli" },
    ],
  },
  {
    label: "Xizmatlar",
    href: "/xizmatlar",
    children: [
      { label: "Virtual qabulxona", href: "/virtual-qabulxona" },
      { label: "HEMIS", href: HEMIS_URL },
      { label: "Scopus", href: "https://www.scopus.com" },
      { label: "Doctorium", href: "https://doctorium.com" },
      { label: "Karyera markazi", href: "/karyera" },
      { label: "Korrupsiyaga qarshi kurash", href: "/about/korrupsiyaga-qarshi-kurashish-davlat-dasturlari" },
    ],
  },
  {
    label: "Aloqa",
    href: "/aloqa",
    children: [
      { label: "Kontakt maʻlumotlari", href: "/aloqa" },
      { label: "Xarita", href: "/aloqa#map" },
      { label: "Fuqarolar murojaati", href: "/virtual-qabulxona" },
      { label: "Matbuot xizmati", href: "/aloqa/matbuot" },
    ],
  },
];
