"""Seeds the six quick tool buttons of the home page's top section ("Tezkor xizmatlar": virtual reception, admission,
path finder, online tests, HEMIS, contact) with what the frontend used to hard-code, so the admin panel opens on the
current buttons. Texts the editors already changed in "Sayt matnlari" (hero.tools.<key>.title / .desc) are carried
over. Runs only while there is no tool yet."""
from django.db import migrations

TOOLS = [
    {
        "key": "vq", "icon": "ri-chat-smile-3-line", "url": "/virtual-reception/17", "accent": False,
        "title": {"uz": "Virtual qabulxona", "ru": "Виртуальная приёмная", "en": "Virtual reception"},
        "desc": {
            "uz": "Rasmiy murojaat yuboring va javobni kuzating.",
            "ru": "Отправьте официальное обращение и отследите ответ.",
            "en": "Send an official request and track the reply.",
        },
    },
    {
        "key": "admit", "icon": "ri-file-user-line", "url": "/qabul", "accent": True,
        "title": {"uz": "Qabul 2026", "ru": "Приём 2026", "en": "Admissions 2026"},
        "desc": {
            "uz": "Yoʻnalishlar, hujjatlar va onlayn ariza.",
            "ru": "Направления, документы и онлайн-заявка.",
            "en": "Tracks, documents and online application.",
        },
    },
    {
        "key": "path", "icon": "ri-route-line", "url": "#pathfinder", "accent": False,
        "title": {"uz": "Yoʻnalish tanlash", "ru": "Выбор направления", "en": "Path finder"},
        "desc": {
            "uz": "2 daqiqada sizga mos taʻlim yoʻlini toping.",
            "ru": "За 2 минуты найдите подходящий путь обучения.",
            "en": "Find the study path that fits you in 2 minutes.",
        },
    },
    {
        "key": "test", "icon": "ri-questionnaire-line", "url": "https://online-imtixon.uz", "accent": False,
        "title": {"uz": "Onlayn testlar", "ru": "Онлайн-тесты", "en": "Online tests"},
        "desc": {
            "uz": "iTest — imtihonga tayyorgarlik platformasi.",
            "ru": "iTest — платформа подготовки к экзаменам.",
            "en": "iTest — prep platform for exams.",
        },
    },
    {
        "key": "hemis", "icon": "ri-dashboard-3-line", "url": "https://hemis.fjsti.uz", "accent": False,
        "title": {"uz": "HEMIS", "ru": "HEMIS", "en": "HEMIS"},
        "desc": {
            "uz": "Baholar, jadval va shaxsiy kabinet.",
            "ru": "Оценки, расписание и личный кабинет.",
            "en": "Grades, timetable and student portal.",
        },
    },
    {
        "key": "contact", "icon": "ri-map-pin-line", "url": "/aloqa", "accent": False,
        "title": {"uz": "Aloqa", "ru": "Контакты", "en": "Contact"},
        "desc": {
            "uz": "Manzil, telefon va xabar qoldirish.",
            "ru": "Адрес, телефон и форма сообщения.",
            "en": "Address, phone and message form.",
        },
    },
]


def seed(apps, schema_editor):
    HomeItem = apps.get_model("site_settings", "HomeItem")
    SiteText = apps.get_model("site_settings", "SiteText")
    if HomeItem.objects.filter(section="tool").exists():
        return
    edited = {row.key: row for row in SiteText.objects.filter(key__startswith="hero.tools.")}
    for order, tool in enumerate(TOOLS, start=1):
        fields = {
            "section": "tool",
            "order": order,
            "icon": tool["icon"],
            "url": tool["url"],
            "value": "accent" if tool["accent"] else "",
        }
        for lang in ("uz", "ru", "en"):
            fields[f"title_{lang}"] = tool["title"][lang]
            fields[f"text_{lang}"] = tool["desc"][lang]
        for field, suffix in (("title", "title"), ("text", "desc")):
            row = edited.get(f"hero.tools.{tool['key']}.{suffix}")
            if row is None:
                continue
            for lang in ("uz", "ru", "en"):
                value = getattr(row, f"text_{lang}").strip()
                if value:
                    fields[f"{field}_{lang}"] = value
        HomeItem.objects.create(**fields)


class Migration(migrations.Migration):
    dependencies = [("site_settings", "0006_homeitem_tool_section")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
