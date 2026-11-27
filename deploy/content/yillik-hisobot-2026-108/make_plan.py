"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-108/make_plan.py

Old pages whose Russian / English text differs in STRUCTURE from the Uzbek one (found by comparing, block by block, the number of links, list items and table cells in the three
languages of the 238 pages of the menu). Every op replaces the one block at `order` (count 1; "old": what it is now, "new": what it becomes). What is done:
  * the Uzbek text has a link that the Russian / English text does not: the same address is put round the same words (davlat-dasturlari, ordinatura-* addresses, kop-berilayotgan-savollar,
    oqishni-kochirish-qayta-tiklash, qabul-nizomi-2, registrator-ofisi, talim-sifatini-nazorat-qilish-bolimi); pieces of one link split in two or three are joined;
  * eng-kop-beriladigan-savollar #15: the English list has a third item that is a rough second copy of block #16 (present in all three languages): removed;
  * oqitishning-texnik-vositalar-bolimi #2: the Uzbek item 2 holds two items that ru/en have apart: split in two (words unchanged);
  * study-in-uzbekistan #3: a link to the home page only in English: removed;
  * magistratura-online-royxatdan-otish-2025 #4/#5: the ru/en texts are one place behind the Uzbek ones (ru/en lack the paragraph about diplom.edu.uz and cut the next title in two): ru/en #4 = a TRANSLATION
    of the Uzbek paragraph (written by Claude, to be read by the staff), ru/en #5 = the whole title;
  * ordinatura-test-sinovi-manzillari-2025 #27: the ru/en sentence was spoiled ("tmbm.ssv.uz hours", "from site 1"): rewritten with the same facts as the Uzbek one (Claude's wording);
  * yoriqnoma-klinik-ordinatura #18/#19: ru/en say in the lead-in who is dismissed and by whom, the Uzbek puts the consequence as a fourth list item after a dash: the Uzbek lead-in and list are
    made like ru/en (the words of the Uzbek consequence, moved to the lead-in: written by Claude, to be read by the staff).
Left as they are on purpose: the notes "the text of the act is in Uzbek" (ru/en only) of ilmiy-faoliyat-... #11, oliy-talim-... #7 / #6."""
import copy
import json
import re
import subprocess
from pathlib import Path

LANGS = ("uz", "ru", "en")
ops = []
cache = {}


def blocks_of(slug):
    if slug not in cache:
        d = json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % slug], capture_output=True, text=True, check=True).stdout)
        cache[slug] = {b["order"]: b for b in d["blocks"]}
    return cache[slug]


def op(slug, order, edit):
    b = blocks_of(slug)[order]
    new = copy.deepcopy(b["data"])
    edit(new)
    assert new != b["data"], (slug, order)
    ops.append({"slug": slug, "order": order, "count": 1, "old": [{"block_type": b["block_type"], "data": b["data"]}], "new": [{"block_type": b["block_type"], "data": new}]})


def link(text, phrase, url, nth=1):
    """`phrase` (its nth plain occurrence) becomes [phrase](url)."""
    assert "](" not in text or text.count("[") == 0 or True
    spots = [m.start() for m in re.finditer(re.escape(phrase), text)]
    assert len(spots) >= nth, (phrase, text[:80])
    i = spots[nth - 1]
    assert text[max(0, i - 1):i] != "[", phrase
    return text[:i] + "[%s](%s)" % (phrase, url) + text[i + len(phrase):]


def whole_link_of(text):
    m = re.fullmatch(r"\[(.+)\]\((\S+?)\)([.;,]?)", text.strip(), re.S)
    return m.groups() if m else None


# ---- davlat-dasturlari ----------------------------------------------------------------------------------------------------------------------
S = "davlat-dasturlari"
url1 = re.search(r"\]\((\S+?)\)", blocks_of(S)[1]["data"]["ru"]["text"]).group(1)


def davlat1(d):
    d["uz"]["text"] = "[%s](%s)" % (d["uz"]["text"], url1)
    d["ru"]["text"] = "[2025 год - Год охраны окружающей среды и «зеленой экономики»](%s)" % url1
    d["en"]["text"] = "[%s](%s)" % (d["en"]["text"], url1)


op(S, 1, davlat1)


def davlat2(d):
    for lang in ("ru", "en"):
        t = d[lang]["text"]
        while True:
            n = re.sub(r"\[([^\]]*)\]\((\S+?)\)\s*\[([^\]]*)\]\(\2\)", lambda m: "[%s %s](%s)" % (m.group(1), m.group(3), m.group(2)), t)
            if n == t:
                break
            t = n
        d[lang]["text"] = t


op(S, 2, davlat2)

# ---- the addresses of the two ordinatura pages: the whole line is the link -----------------------------------------------------------------
for S in ("ordinatura-qabul-komissiyasi-yangiliklari-2025", "ordinatura-test-sinovi-manzillari-2025"):
    for order, b in sorted(blocks_of(S).items()):
        if b["block_type"] != "paragraph":
            continue
        wl = whole_link_of(b["data"]["uz"]["text"])
        if wl and "[" not in b["data"]["ru"]["text"] and "[" not in b["data"]["en"]["text"]:
            def addr(d, url=wl[1], tail=wl[2]):
                for lang in ("ru", "en"):
                    t = d[lang]["text"]
                    if tail and t.endswith(tail):
                        d[lang]["text"] = "[%s](%s)%s" % (t[: -len(tail)], url, tail)
                    else:
                        d[lang]["text"] = "[%s](%s)" % (t, url)
            op(S, order, addr)

# ---- kop-berilayotgan-savollar: the agency's site -------------------------------------------------------------------------------------------
S = "kop-berilayotgan-savollar"
UZBMB = "https://uzbmb.uz/"
RU_AG, EN_AG = "Агентство по оценке знаний и квалификаций", "Knowledge and Skills Assessment Agency"


def agency(en_phrase):
    def edit(d):
        d["ru"]["text"] = link(d["ru"]["text"], RU_AG, UZBMB, nth=1 if "Агентство" in d["ru"]["text"] else 1)
        d["en"]["text"] = link(d["en"]["text"], en_phrase, UZBMB)
    return edit


op(S, 3, agency(EN_AG))
op(S, 7, agency("State Testing Center"))
op(S, 11, agency(EN_AG))

# ---- oqishni-kochirish-qayta-tiklash --------------------------------------------------------------------------------------------------------
S = "oqishni-kochirish-qayta-tiklash"
TR = "http://transfer.edu.uz/"
op(S, 5, lambda d: d.update(ru={**d["ru"], "text": link(d["ru"]["text"], "transfer.dtm.uz", TR)}, en={**d["en"], "text": link(d["en"]["text"], "transfer.dtm.uz", TR)}))
op(S, 6, lambda d: d.update(ru={**d["ru"], "text": link(d["ru"]["text"], "transfer.edu.uz", TR)}, en={**d["en"], "text": link(d["en"]["text"], "transfer.edu.uz", TR)}))

# ---- qabul-nizomi-2 #5, item 0 ----------------------------------------------------------------------------------------------------------------
S = "qabul-nizomi-2"
u = re.search(r"\]\((\S+?)\)", blocks_of(S)[5]["data"]["uz"]["items"][0]).group(1)


def nizom(d):
    d["ru"]["items"][0] = d["ru"]["items"][0].replace("проводятся тестовые", "[проводятся](%s) тестовые" % u, 1)
    d["en"]["items"][0] = d["en"]["items"][0].replace("will be administered", "will be [administered](%s)" % u, 1)


op(S, 5, nizom)

# ---- registrator-ofisi ------------------------------------------------------------------------------------------------------------------------
op("registrator-ofisi", 2, lambda d: [d[l].update(text=d[l]["text"].replace("https://hemis.fjsti.uz/", "[https://hemis.fjsti.uz/](https://hemis.fjsti.uz/)", 1)) for l in ("ru", "en")])

# ---- talim-sifatini-nazorat-qilish-bolimi -----------------------------------------------------------------------------------------------------
S = "talim-sifatini-nazorat-qilish-bolimi"
uzl = re.findall(r"\[([^\]]+)\]\((\S+?)\)", blocks_of(S)[2]["data"]["uz"]["text"])
assert len(uzl) == 3
(_, u_law), (_, u_prog), (_, u_dec) = uzl


def sifat(d):
    t = d["ru"]["text"]
    t = link(t, "Об образовании", u_law)
    t = link(t, "О Национальной программе подготовки кадров", u_prog)
    t = link(t, "20 апреля 2017 года № ПП-2909", u_dec)
    d["ru"]["text"] = t
    t = d["en"]["text"]
    t = link(t, "On Education", u_law)
    t = link(t, "On the National Program for Personnel Training", u_prog)
    t = link(t, "April 20, 2017, No. PP-2909", u_dec)
    d["en"]["text"] = t


op(S, 2, sifat)

# ---- study-in-uzbekistan #3 --------------------------------------------------------------------------------------------------------------------
op("study-in-uzbekistan", 3, lambda d: d["en"].update(text=d["en"]["text"].replace("([FMIOPH](/))", "(FMIOPH)")))

# ---- eng-kop-beriladigan-savollar #15: the third English item repeats block #16 --------------------------------------------------------------
S = "eng-kop-beriladigan-savollar"
assert blocks_of(S)[15]["data"]["en"]["items"][2].startswith("Graduates of master's and clinical residencies studying")
op(S, 15, lambda d: d["en"].update(items=d["en"]["items"][:2]))

# ---- oqitishning-texnik-vositalar-bolimi #2: one Uzbek item holds two --------------------------------------------------------------------------
S = "oqitishning-texnik-vositalar-bolimi"


def split_item(d):
    item = d["uz"]["items"][1]
    cut = " Institut oʻquv jarayonida zamonaviy texnik oʻquv qoʻllanmalaridan foydalanishni tashkil etish."
    assert item.endswith(cut)
    d["uz"]["items"][1:2] = [item[: -len(cut)], cut.strip()]


op(S, 2, split_item)

# ---- magistratura-online-royxatdan-otish-2025 #4, #5 ---------------------------------------------------------------------------------------------
S = "magistratura-online-royxatdan-otish-2025"
assert blocks_of(S)[4]["data"]["ru"]["text"].startswith("Национальные и международно-признанные сертификаты")
DIPLOM = "http://diplom.edu.uz"
RU4 = "Для абитуриентов созданы значительные удобства, например, абитуриент может автоматически загрузить данные диплома через платформу HEMIS или сайт [diplom.edu.uz](%s)." % DIPLOM
EN4 = "Considerable conveniences have been developed for applicants; for example, an applicant can automatically download diploma data through the HEMIS platform or the [diplom.edu.uz](%s) website." % DIPLOM
RU5 = "Национальные и международно-признанные сертификаты, оценивающие уровень владения иностранными языками, необходимые для поступления в магистратуру и докторантуру"
EN5 = "National and internationally recognized certificates assessing the level of knowledge of foreign languages required for applying for master's and doctoral studies"
op(S, 4, lambda d: (d["ru"].update(text=RU4), d["en"].update(text=EN4)))
assert blocks_of(S)[5]["data"]["ru"]["text"] == "в магистратуру и докторантуру" and blocks_of(S)[5]["data"]["en"]["text"] == "and doctoral studies"
op(S, 5, lambda d: (d["ru"].update(text=RU5), d["en"].update(text=EN5)))

# ---- yoriqnoma-klinik-ordinatura #18, #19 ---------------------------------------------------------------------------------------------------------
S = "yoriqnoma-klinik-ordinatura"
assert blocks_of(S)[18]["data"]["uz"]["text"] == "Talabalar:"
UZ18 = "Klinik ordinator kafedra mudiri taqdimnomasiga asosan muassasa rahbarining buyrugʻi bilan quyidagi hollarda ordinaturadan chetlashtiriladi, agar u:"
op(S, 18, lambda d: d["uz"].update(text=UZ18))


def yor19(d):
    items = d["uz"]["items"]
    assert len(items) == 4 and items[2].endswith(" —") and items[3].startswith("kafedra mudiri taqdimnomasiga")
    d["uz"]["items"] = [items[0], items[1], items[2][:-2].rstrip() + "."]


op(S, 19, yor19)

# ---- ordinatura-test-sinovi-manzillari-2025 #27: the ru/en sentence was spoiled (the address of the site stands where "1 hour" belongs, "1" where the site belongs) ----
S = "ordinatura-test-sinovi-manzillari-2025"
u27 = re.search(r"\]\((\S+?)\)", blocks_of(S)[27]["data"]["uz"]["text"]).group(1)
assert "tmbm.ssv.uz часа" in blocks_of(S)[27]["data"]["ru"]["text"] and "tmbm.ssv.uz hours" in blocks_of(S)[27]["data"]["en"]["text"]
RU27 = ("ВНИМАНИЕ! Напоминание! Сдача тестовых испытаний начинается 26-29 августа в 7:00, претендентов просят прибыть на адрес экзаменов не позднее чем за 1 час до начала экзаменов "
        "с разрешением, загруженным с сайта [tmbm.ssv.uz](%s), и оригиналом документа, удостоверяющего личность." % u27)
EN27 = ("ATTENTION! Reminder! Passing tests begins on August 26-29 at 7:00; applicants are asked to arrive at the exam address no later than 1 hour before the start of the exams "
        "with a permit downloaded from the website [tmbm.ssv.uz](%s) and the original identity document." % u27)
op(S, 27, lambda d: (d["ru"].update(text=RU27), d["en"].update(text=EN27)))

Path("deploy/content/yillik-hisobot-2026-108/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "ops")
for o in ops:
    print(o["slug"], "#%d" % o["order"])
