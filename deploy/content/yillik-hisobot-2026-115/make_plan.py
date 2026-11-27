"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-115/make_plan.py

"The Russian page must be Russian" (the user, 2026-11-27): the titles of the 156 video lessons of klinik-fikrlashga-doir-video-darslar (seven lists, each a link to a YouTube video) were English in
Russian too, and the list of topics of the biochemistry department (department-7 #49) repeats 24 of them. Russian gets Russian titles (Claude's translation, standard terms), the links stay, English and
Uzbek stay as they are. (The videos themselves are English.) Every op replaces the one block at `order` ("old": what it is now, "new": what it becomes)."""
import copy
import json
import re
import subprocess
import time
from pathlib import Path

RU = {
    "Renal Anatomy": "Анатомия почек", "Renal physiology": "Физиология почек", "Renal Physiology 2": "Физиология почек 2", "Nephron physiology": "Физиология нефрона",
    "Renal Endocrinology": "Эндокринология почек", "Acid excretion": "Выведение кислот", "Acid Base Principles": "Основы кислотно-щелочного баланса",
    "Respiratory Acid Base disorders": "Респираторные нарушения кислотно-щелочного баланса", "Metabolic Alkalosis": "Метаболический алкалоз", "Metabolic Acidosis": "Метаболический ацидоз",
    "Renal Tubular Acidosis": "Почечный канальцевый ацидоз", "Acid Base Problems": "Задачи по кислотно-щелочному балансу", "Electrolytes": "Электролиты",
    "Sodium and Water Balance": "Баланс натрия и воды", "Sodium Disorders": "Нарушения обмена натрия", "Glomerular Disease Principles": "Основы болезней клубочков",
    "Nephritic Syndrome": "Нефритический синдром", "Nephrotic Syndrome": "Нефротический синдром", "MPGN": "Мембранопролиферативный гломерулонефрит",
    "Tubulointerstitial Disorders": "Тубулоинтерстициальные заболевания", "Renal Failure": "Почечная недостаточность", "Urinary Infections": "Инфекции мочевыводящих путей",
    "Cystic Kidney Diseases": "Кистозные болезни почек", "Diuretics": "Диуретики", "Kidney Stones": "Камни в почках", "Renal and Bladder Malignancies": "Злокачественные опухоли почек и мочевого пузыря",
    "Rhabdomyolysis": "Рабдомиолиз",
    "Genetic Principles": "Основы генетики", "Genetic Mapping": "Генетическое картирование", "Meiosis": "Мейоз", "Hardy-Weinberg Law": "Закон Харди–Вайнберга", "Pedigrees": "Родословные",
    "Imprinting": "Импринтинг", "Down Syndrome": "Синдром Дауна", "Trisomy": "Трисомия", "Muscular Dystrophies": "Мышечные дистрофии",
    "Trinucleotide Repeat Disorders": "Болезни тринуклеотидных повторов", "Deletion Syndromes": "Делеционные синдромы", "Klinefelter and Turner Syndromes": "Синдромы Клайнфельтера и Тёрнера",
    "Coagulation": "Свёртывание крови", "Platelet Activation": "Активация тромбоцитов", "Hypercoagulable States": "Гиперкоагуляционные состояния", "Coagulopathies": "Коагулопатии",
    "Platelet Disorders": "Заболевания тромбоцитов", "Antiplatelets": "Антиагреганты", "Anticoagulant Drugs": "Антикоагулянты", "Hemolysis Basics": "Основы гемолиза",
    "Extrinsic Hemolysis": "Экстракорпускулярный гемолиз", "Intrinsic Hemolysis": "Внутрикорпускулярный гемолиз", "Microcytic Anemias": "Микроцитарные анемии", "Thalassemias": "Талассемии",
    "Sickle Cell Anemia": "Серповидноклеточная анемия", "Other Anemias": "Другие анемии", "Blood Groups": "Группы крови", "Acute Leukemias": "Острые лейкозы", "Chronic Leukemias": "Хронические лейкозы",
    "Hodgkin Lymphoma": "Лимфома Ходжкина", "Non Hodgkin Lymphoma": "Неходжкинские лимфомы", "Plasma Cell Disorders": "Плазмоклеточные заболевания", "Amyloidosis": "Амилоидоз",
    "Myeloproliferative Disorders": "Миелопролиферативные заболевания", "Antimetabolites": "Антиметаболиты", "Alkylating Agents": "Алкилирующие агенты",
    "Antitumor Antibiotics": "Противоопухолевые антибиотики", "Microtubule Inhibitors": "Ингибиторы микротрубочек", "DNA Drugs": "Препараты, действующие на ДНК",
    "Other Cancer Drugs": "Другие противоопухолевые препараты", "Porphyrias": "Порфирии",
    "DNA Replication": "Репликация ДНК", "DNA Mutations": "Мутации ДНК", "DNA Repair": "Репарация ДНК", "Transcription": "Транскрипция", "Translation": "Трансляция",
    "Polymerase Chain Reaction": "Полимеразная цепная реакция", "Blotting": "Блоттинг", "Flow Cytometry": "Проточная цитометрия", "ELISA": "ИФА (ELISA)", "Microarrays and FISH": "Микрочипы и FISH",
    "Cell Cycle": "Клеточный цикл", "Cell Structure": "Строение клетки", "Cytoskeleton": "Цитоскелет", "Connective Tissue": "Соединительная ткань",
    "Bacteria": "Бактерии", "Shapes and Stains": "Формы и окраска", "Bacterial Culture": "Культивирование бактерий", "Special Growth Requirements": "Особые условия роста", "Virulence": "Вирулентность",
    "Growth and Genetics": "Рост и генетика", "Bacterial Identification": "Идентификация бактерий", "Staphylococci": "Стафилококки", "Streptococci": "Стрептококки",
    "Other Gram Positives": "Другие грамположительные бактерии", "Gram Negative Rods": "Грамотрицательные палочки", "Other Gram Negatives": "Другие грамотрицательные бактерии",
    "Spirochetes": "Спирохеты", "Zoonotic Bacteria": "Зоонозные бактерии", "Mycobacteria": "Микобактерии", "Penicillins": "Пенициллины", "β-Lactam Antibiotics": "β-лактамные антибиотики",
    "Sulfonamides": "Сульфаниламиды", "Protein Synthesis Inhibitors": "Ингибиторы синтеза белка", "Other Antibiotics": "Другие антибиотики", "Fungal Pneumonias": "Грибковые пневмонии",
    "Fungal Skin Infections": "Грибковые инфекции кожи", "Opportunistic Fungal Infections": "Оппортунистические грибковые инфекции", "Antifungal Drugs": "Противогрибковые препараты",
    "Malaria": "Малярия", "Protozoa": "Простейшие", "Helminths": "Гельминты", "Virus Structures": "Строение вирусов", "DNA Viruses": "ДНК-вирусы", "Herpes Viruses": "Вирусы герпеса",
    "RNA Viruses": "РНК-вирусы", "Viral Hepatitis": "Вирусные гепатиты", "HIV": "ВИЧ", "HIV Drugs": "Препараты против ВИЧ", "Antivirals": "Противовирусные препараты",
    "Purine Metabolism": "Метаболизм пуринов", "Pyrimidine Metabolism": "Метаболизм пиримидинов", "Glucose": "Глюкоза", "Glycolysis": "Гликолиз", "Gluconeogenesis": "Глюконеогенез",
    "Glycogen": "Гликоген", "HMP Shunt": "Гексозомонофосфатный шунт", "Fructose and Galactose": "Фруктоза и галактоза", "Pyruvate Dehydrogenase": "Пируватдегидрогеназа",
    "TCA Cycle": "Цикл трикарбоновых кислот", "Electron Transport Chain": "Электрон-транспортная цепь", "Fatty Acids": "Жирные кислоты", "Ketone Bodies": "Кетоновые тела",
    "Ethanol Metabolism": "Метаболизм этанола", "Exercise and Starvation": "Физическая нагрузка и голодание", "Inborn Errors of Metabolism": "Врождённые нарушения обмена веществ",
    "Amino Acids": "Аминокислоты", "Phenylalanine and Tyrosine": "Фенилаланин и тирозин", "Other Amino Acids": "Другие аминокислоты", "Ammonia": "Аммиак", "B Vitamins": "Витамины группы B",
    "Folate and Vitamin B12": "Фолат и витамин B12", "Other Vitamins": "Другие витамины", "Lipid Metabolism": "Метаболизм липидов", "Hyperlipidemia": "Гиперлипидемия",
    "Lipid Drugs": "Липидснижающие препараты", "Lysosomal Storage Diseases": "Лизосомные болезни накопления",
    "Shoulder and Elbow": "Плечо и локоть", "Brachial Plexus": "Плечевое сплетение", "Wrist": "Запястье", "Hand": "Кисть", "Lumbosacral Plexus": "Пояснично-крестцовое сплетение",
    "Lumbar Radiculopathy": "Поясничная радикулопатия", "Hip": "Тазобедренный сустав", "Skeletal Muscle": "Скелетные мышцы", "Cardiac Muscle": "Сердечная мышца", "Smooth Muscle": "Гладкие мышцы",
    "Bone": "Кость", "Bone Disorders": "Заболевания костей", "Osteoporosis": "Остеопороз", "Osteoporosis Drugs": "Препараты при остеопорозе", "Bone Tumors": "Опухоли костей",
    "Osteoarthritis": "Остеоартрит", "Gout": "Подагра", "Gout Drugs": "Препараты при подагре", "CPPD": "Болезнь депонирования пирофосфата кальция (CPPD)",
    "Seronegative Spondyloarthritis": "Серонегативные спондилоартриты", "Muscle Disorders": "Заболевания мышц", "Neuromuscular Disorders": "Нервно-мышечные заболевания",
    "DNA Structure": "Структура ДНК", "Lipid": "Липиды",
}
LINK = re.compile(r"^\[(.*)\]\((.*)\)$")


def api(path):
    for _ in range(5):
        text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/" + path + ("&" if "?" in path else "?") + "v=115"], capture_output=True, text=True).stdout
        try:
            return json.loads(text)
        except ValueError:
            time.sleep(3)
    raise SystemExit("API did not answer: " + path)


def russian(item):
    match = LINK.match(item)
    title = match.group(1) if match else item
    return ("[%s](%s)" % (RU[title], match.group(2))) if match else RU[title]


ops = []
SLUG = "klinik-fikrlashga-doir-video-darslar"
count = 0
for block in sorted(api("pages/%s/" % SLUG)["blocks"], key=lambda b: b["order"]):
    if block["block_type"] != "list":
        continue
    data = block["data"]
    assert data["ru"]["items"] == data["uz"]["items"]
    new = copy.deepcopy(data)
    new["ru"]["items"] = [russian(i) for i in data["uz"]["items"]]
    count += len(new["ru"]["items"])
    ops.append({"slug": SLUG, "order": block["order"], "count": 1, "old": [{"block_type": "list", "data": data}], "new": [{"block_type": "list", "data": new}]})

dep = api("departments/tibbiy-va-biologik-kimyo-kafedrasi/")
dep = dep.get("data", dep)["page"]
block = {b["order"]: b for b in dep["blocks"]}[49]
data = block["data"]
assert block["block_type"] == "list" and data["uz"]["items"][0] == "Folate and Vitamin B12" and data["ru"]["items"][0] == "olate and Vitamin B12"
new = copy.deepcopy(data)
new["ru"]["items"] = [RU[i] for i in data["uz"]["items"]]
count += len(new["ru"]["items"])
ops.append({"slug": dep["slug"], "order": 49, "count": 1, "old": [{"block_type": "list", "data": data}], "new": [{"block_type": "list", "data": new}]})

Path("deploy/content/yillik-hisobot-2026-115/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "blocks,", count, "titles")
