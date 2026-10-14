"""Seeds the home-page lists (partners, projects, student quotes, figures, "why us" cards) with exactly what the
frontend used to hard-code, so the admin panel opens on the current content and every line can be edited or deleted.

Interface texts the editors had already changed in "Sayt matnlari" (SiteText rows such as partners.item1.name) are
carried over, so nothing they edited is lost. Runs only while the table is empty."""
from django.db import migrations

ITEMS = [{'section': 'partner',
  'order': 1,
  'title': {'uz': 'Prezident portali', 'ru': 'Портал Президента', 'en': "President's Portal"},
  'icon': 'ri-government-line',
  'url': 'https://president.uz/uz'},
 {'section': 'partner',
  'order': 2,
  'title': {'uz': 'Qonun hujjatlari maʻlumotlar bazasi',
            'ru': 'База данных нормативно-правовых актов',
            'en': 'Legal Database'},
  'icon': 'ri-file-list-line',
  'url': 'https://lex.uz/'},
 {'section': 'partner',
  'order': 3,
  'title': {'uz': 'Hukumat portali', 'ru': 'Портал Правительства', 'en': 'Government Portal'},
  'icon': 'ri-building-line',
  'url': 'https://gov.uz/uz'},
 {'section': 'partner',
  'order': 4,
  'title': {'uz': 'Vazirlik (OTMFI)',
            'ru': 'Министерство высшего образования',
            'en': 'Ministry of Higher Education'},
  'icon': 'ri-graduation-cap-line',
  'url': 'https://gov.uz/en/edu'},
 {'section': 'partner',
  'order': 5,
  'title': {'uz': 'SSV', 'ru': 'Министерство здравоохранения', 'en': 'Ministry of Health'},
  'icon': 'ri-heart-pulse-line',
  'url': 'https://ssv.uz/uz'},
 {'section': 'partner',
  'order': 6,
  'title': {'uz': 'Study in Uzbekistan', 'ru': 'Study in Uzbekistan', 'en': 'Study in Uzbekistan'},
  'icon': 'ri-global-line',
  'url': 'https://studyin-uzbekistan.uz/universities/80'},
 {'section': 'partner',
  'order': 7,
  'title': {'uz': 'Korrupsiyaga qarshi', 'ru': 'Противодействие коррупции', 'en': 'Anti-Corruption'},
  'icon': 'ri-shield-check-line',
  'url': '/about/korrupsiyaga-qarshi-kurashish-davlat-dasturlari'},
 {'section': 'partner',
  'order': 8,
  'title': {'uz': 'HEMIS', 'ru': 'HEMIS', 'en': 'HEMIS'},
  'icon': 'ri-database-2-line',
  'url': 'https://hemis.fjsti.uz'},
 {'section': 'project',
  'order': 1,
  'title': {'uz': 'AiShifokor', 'ru': 'AiShifokor', 'en': 'AiShifokor'},
  'url': 'https://aishifokor.uz',
  'icon': 'ri-heart-pulse-line',
  'image_path': '/images/projects/aishifokor.jpg'},
 {'section': 'project',
  'order': 2,
  'title': {'uz': 'iMentor', 'ru': 'iMentor', 'en': 'iMentor'},
  'url': 'https://imentor.uz',
  'icon': 'ri-user-star-line',
  'image_path': '/images/projects/imentor.jpg'},
 {'section': 'project',
  'order': 3,
  'title': {'uz': 'iTest', 'ru': 'iTest', 'en': 'iTest'},
  'url': 'https://online-imtixon.uz',
  'icon': 'ri-questionnaire-line',
  'image_path': '/images/projects/itest.jpg'},
 {'section': 'project',
  'order': 4,
  'title': {'uz': 'Teletibbiyot', 'ru': 'Телемедицина', 'en': 'Telemedicine'},
  'url': '',
  'icon': 'ri-vidicon-line',
  'image_path': '/images/projects/teletibbiyot.jpg'},
 {'section': 'project',
  'order': 5,
  'title': {'uz': 'Silikonli mahsulot', 'ru': 'Силиконовая продукция', 'en': 'Silicone products'},
  'url': '',
  'icon': 'ri-cpu-line',
  'image_path': '/images/projects/slikon.jpg'},
 {'section': 'project',
  'order': 6,
  'title': {'uz': 'iCamera', 'ru': 'iCamera', 'en': 'iCamera'},
  'url': '',
  'icon': 'ri-camera-line',
  'image_path': '/images/projects/icamera.jpg'},
 {'section': 'voice',
  'order': 1,
  'text': {'uz': 'Bu yerda nazariya bilan klinik amaliyot yonma-yon. Birinchi kursdayoq oʻzini shifokordek '
                 'his qilasiz.',
           'ru': 'Здесь теория и клиническая практика идут рядом. Уже с первого курса чувствуешь себя '
                 'врачом.',
           'en': 'Theory and clinical practice go side by side here. You feel like a doctor from year one.'},
  'title': {'uz': 'Madina Aliyeva', 'ru': 'Мадина Алиева', 'en': 'Madina Aliyeva'},
  'subtitle': {'uz': '3-kurs talabasi · Davolash ishi',
               'ru': '3 курс · Лечебное дело',
               'en': '3rd-year student · General medicine'}},
 {'section': 'voice',
  'order': 2,
  'text': {'uz': 'Professorlar haqiqiy mentor. Amaliyotdan keyin ishga joylashish ancha oson boʻldi.',
           'ru': 'Преподаватели — настоящие наставники. После практики устроиться на работу стало проще.',
           'en': 'Professors are real mentors. After practice, finding a job became much easier.'},
  'title': {'uz': 'Sardor Normatov', 'ru': 'Сардор Норматов', 'en': 'Sardor Normatov'},
  'subtitle': {'uz': 'Bitiruvchi · 2024', 'ru': 'Выпускник · 2024', 'en': 'Graduate · 2024'}},
 {'section': 'voice',
  'order': 3,
  'text': {'uz': 'Xorijiy seminarlar va til muhiti menga ishonch berdi. Endi xalqaro loyihalarga '
                 'qoʻshilaman.',
           'ru': 'Международные семинары и языковая среда дали уверенность для глобальных проектов.',
           'en': 'International seminars and the language environment gave me confidence for global '
                 'projects.'},
  'title': {'uz': 'Dilnoza Karimova', 'ru': 'Дильноза Каримова', 'en': 'Dilnoza Karimova'},
  'subtitle': {'uz': '4-kurs · Jamoat salomatligi',
               'ru': '4 курс · Общественное здоровье',
               'en': '4th year · Public health'}},
 {'section': 'voice',
  'order': 4,
  'text': {'uz': 'Ordinaturada real klinik vaziyatlar — eng yaxshi oʻqituvchi. FerMI shuni beradi.',
           'ru': 'В ординатуре реальные клинические случаи — лучший учитель. FerMI это даёт.',
           'en': 'In residency, real clinical cases are the best teacher. FerMI delivers that.'},
  'title': {'uz': 'Yusuf Rahimov', 'ru': 'Юсуф Рахимов', 'en': 'Yusuf Rahimov'},
  'subtitle': {'uz': 'Klinik ordinator', 'ru': 'Клинический ординатор', 'en': 'Clinical resident'}},
 {'section': 'fact',
  'order': 1,
  'value': '92%',
  'title': {'uz': 'Bitiruvchilar bandligi', 'ru': 'Трудоустройство', 'en': 'Graduate employment'}},
 {'section': 'fact',
  'order': 2,
  'value': '4.9',
  'title': {'uz': 'Talabalar bahosi', 'ru': 'Оценка студентов', 'en': 'Student rating'}},
 {'section': 'fact',
  'order': 3,
  'value': '20+',
  'title': {'uz': 'Klinik hamkorlik', 'ru': 'Клинические партнёры', 'en': 'Clinical partners'}},
 {'section': 'fact',
  'order': 4,
  'value': '15+',
  'title': {'uz': 'Xalqaro hamkor', 'ru': 'Международные партнёры', 'en': 'International partners'}},
 {'section': 'why',
  'order': 1,
  'title': {'uz': 'Zamonaviy taʻlim', 'ru': 'Современное образование', 'en': 'Modern education'},
  'text': {'uz': 'Simulyatsiya, raqamli platformalar va interaktiv dars usullari orqali talaba dastlabki '
                 'kursdanoq professional muhitga kirishadi.',
           'ru': 'Симуляции, цифровые платформы и интерактивные методы с первых курсов погружают студента в '
                 'профессиональную среду.',
           'en': 'Simulation, digital platforms and interactive teaching put students in a professional '
                 'setting from early years.'},
  'value': '100%',
  'subtitle': {'uz': 'Raqamli taʻlim', 'ru': 'Цифровое обучение', 'en': 'Digital learning'}},
 {'section': 'why',
  'order': 2,
  'title': {'uz': 'Malakali professorlar',
            'ru': 'Квалифицированные профессора',
            'en': 'Qualified professors'},
  'text': {'uz': 'Ilmiy darajali oʻqituvchilar va amaliyotchi shifokorlar talabalarga mentorship beradi — '
                 'har bir guruh eʻtibordan chetda qolmaydi.',
           'ru': 'Преподаватели с учёными степенями и практикующие врачи сопровождают каждую группу.',
           'en': 'Faculty with academic degrees and practicing doctors mentor every group closely.'},
  'value': '275+',
  'subtitle': {'uz': 'Professorlar', 'ru': 'Профессора', 'en': 'Professors'}},
 {'section': 'why',
  'order': 3,
  'title': {'uz': 'Amaliyot va tajriba', 'ru': 'Практика и опыт', 'en': 'Practice and experience'},
  'text': {'uz': 'Klinik bazalar va simulyatsiya markazida real vaziyatlar mashq qilinadi. Bitiruvchilar '
                 'ishga tayyor holda chiqadi.',
           'ru': 'Клинические базы и симуляционный центр готовят к реальным ситуациям — выпускники готовы к '
                 'работе.',
           'en': 'Clinical bases and the simulation center train real scenarios so graduates are job-ready.'},
  'value': '20+',
  'subtitle': {'uz': 'Klinik baza', 'ru': 'Клиники', 'en': 'Clinical bases'}},
 {'section': 'why',
  'order': 4,
  'title': {'uz': 'Xalqaro imkoniyatlar',
            'ru': 'Международные возможности',
            'en': 'International opportunities'},
  'text': {'uz': 'Xorijiy universitetlar bilan almashinuv, qoʻshma tadbirlar va ilmiy hamkorlik — talabaga '
                 'global tajriba ochadi.',
           'ru': 'Обмен с зарубежными университетами, совместные мероприятия и наука открывают глобальный '
                 'опыт.',
           'en': 'Exchange with foreign universities, joint events and research open a global path for '
                 'students.'},
  'value': '15+',
  'subtitle': {'uz': 'Hamkorlar', 'ru': 'Партнёры', 'en': 'Partners'}}]

# field of HomeItem -> SiteText key of the same wording, per section ({n} is the item's number)
OVERRIDE_KEYS = {
    "partner": {"title": "partners.item{n}.name"},
    "voice": {"text": "voices.v{n}.quote", "title": "voices.v{n}.name", "subtitle": "voices.v{n}.meta"},
    "fact": {"title": "voices.fact{n}.label"},
    "why": {"title": "whyUs.item{n}.title", "text": "whyUs.item{n}.desc", "subtitle": "whyUs.metric{n}"},
}


def seed(apps, schema_editor):
    HomeItem = apps.get_model("site_settings", "HomeItem")
    SiteText = apps.get_model("site_settings", "SiteText")
    if HomeItem.objects.exists():
        return
    edited = {row.key: row for row in SiteText.objects.all()}
    for item in ITEMS:
        fields = {"section": item["section"], "order": item["order"]}
        for field in ("value", "url", "icon", "image_path"):
            fields[field] = item.get(field, "")
        for field in ("title", "subtitle", "text"):
            for lang in ("uz", "ru", "en"):
                fields[f"{field}_{lang}"] = item.get(field, {}).get(lang, "")
        for field, pattern in OVERRIDE_KEYS.get(item["section"], {}).items():
            row = edited.get(pattern.format(n=item["order"]))
            if row is None:
                continue
            for lang in ("uz", "ru", "en"):
                value = getattr(row, f"text_{lang}").strip()
                if value:
                    fields[f"{field}_{lang}"] = value
        if item["section"] == "fact":
            row = edited.get(f"voices.fact{item['order']}.value")
            if row is not None and row.text_uz.strip():
                fields["value"] = row.text_uz.strip()
        HomeItem.objects.create(**fields)


class Migration(migrations.Migration):
    dependencies = [("site_settings", "0004_homeitem")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
