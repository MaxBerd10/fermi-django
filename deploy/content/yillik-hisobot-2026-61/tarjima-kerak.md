# Script 61 (Tuzilma, Abiturient, Talabalar, Xorijiy-talabalar, Kongress, Interaktiv xizmatlar, Yashil Universitet: 60 pages): what the converter did and what we wrote — please let uz / ru / en readers check it

These pages said the same thing in the three languages block by block, so a generic converter (`deploy/content/_auto_plan.py`) turned their old HTML into typed blocks. It does NOT translate anything: the texts are the old texts, with these changes:

- **Uzbek apostrophes** are U+02BB everywhere. **Old spelling x → h** in a few safe words of the Uzbek texts: Maxkamasi → Mahkamasi, xamkor → hamkor, xozir → hozir, xam → ham, maxalla → mahalla, suxbat → suhbat, isloxot → islohot, xolda → holda, xaqida → haqida, ximoya → himoya, xujjat → hujjat, xar bir/xar kuni → har bir/har kuni, xisob → hisob, xafta → hafta, xayot → hayot, xarakat → harakat. Other old spellings are left (the readers may find more).
- Lines **in CAPITALS** became headings in normal case; a line that is only bold and short became a small heading; lines "1. …", "• …", "– …" one after another became a list (the numbers are gone); a line that is one link to a file became a **document card** (the caption is the link text); bare addresses ("/blog/378/...") and stray signs (">>>") were dropped; YouTube frames stay as a small HTML block.
- **English typos written in Cyrillic** in three pages are fixed ("территории" → "territory", "инициативные" → "proactive", "Мевшсфд" → "Medical").
- **Captions we translated** (they were the same Uzbek or English text in all three languages): `dak-savollari` (ru "Тесты итоговой государственной аттестации", "Задания ОСКЭ…", en "Final state attestation tests", "OSCE tasks…"); `test-markazi-semestr-grafigi` (the five ru captions); `iqtidorli-talabalar` ("Axmadjonova Sarvinoz erishgan yutuqlari" / "Достижения: …" / "Achievements: …", names as in Uzbek); `17-goals-of-un-policies` (16 policy titles in uz and ru, the same as in script 54; the English ones lost the repeated name of the institute).
- The review tool flags "ru is not Cyrillic" for lines that are mostly addresses (links), lists of English video titles (`klinik-fikrlashga-doir-video-darslar`) and lines with e-mail addresses: these are fine.

## Not in this script
`vrachlar-malakasini-oshirish-sertifikati` (tables with merged cells) and the 60 pages whose three languages differ in structure (a Russian page with 3 blocks against 13 in Uzbek, an English page missing, lists of different length...) are written by hand in the next scripts.

## Disk
About 60 pages with pictures and PDFs: the PDFs are copied into `uploads/documents/` (check the server disk).
