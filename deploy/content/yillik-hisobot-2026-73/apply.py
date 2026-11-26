# Moves "how this page is laid out" from the frontend's slug checks into the data (Page.layout, migration content 0008):
#   * 8 regulatory pages (decree + facts table)            -> regulatory
#   * 3 lists of decrees                                    -> regulatory_index
#   * institut-ilmiy-kengashi                               -> council;  ilmiy-kengash -> council_decisions
#   * avtoreferatlar -> abstracts;  tahrir-hayati-kengashi  -> editorial
#   * journal and newspaper archives (jcpm-YYYY, institut-gazetasi-[arxivi-]YYYY) -> archive
#   * eng-kop-beriladigan-savollar                          -> faq
#   * the three conference pages (their lines become a topic list) -> conference
# Nothing about how the pages look changes. Needs `manage.py migrate` first (the layout column).
#
# SAFE BY DESIGN: dry (default) writes nothing; a page is changed only if its layout still is "default" (edited in the admin since -> SKIPPED); apply is one
# transaction with a backup (a second apply is refused); undo puts the old layouts back where they are still the new ones.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-73/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-73/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-73/apply.py
import re

from django.db import connection

from apps.content.migration_tools import run_modes
from apps.content.models import Page

NAME = "yillik-hisobot-2026-73"
BY_SLUG = {
    "talim-togrisia": "regulatory",
    "prezident-farmon-va-qarorlari": "regulatory_index",
    "taraqqiyot-strategiyasi": "regulatory",
    "davlat-dasturlari": "regulatory_index",
    "oliy-talimning-davlat-talim-standarti": "regulatory",
    "oliy-talim-yonalishlari-va-mutaxassisliklari-klassifikatori": "regulatory",
    "ozbeksiton-respublikasi-ssv-buyruqlari": "regulatory_index",
    "ilmiy-faoliyat-boyicha-normativ-huquqiy-hujjatlar": "regulatory",
    "institut-ilmiy-kengashi": "council",
    "ilmiy-kengash": "council_decisions",
    "avtoreferatlar": "abstracts",
    "tahrir-hayati-kengashi": "editorial",
    "eng-kop-beriladigan-savollar": "faq",
}
ARCHIVE = re.compile(r"^(?:jcpm-\d{4}|institut-gazetasi-(?:arxivi-)?\d{4})$")
CONFERENCE = re.compile(r"^(?:xalqaro|ilmiy|respublika-ilmiy)-konferensiyalar(?:i)?$")


def wanted():
    for page in Page.objects.order_by("slug"):
        layout = BY_SLUG.get(page.slug) or ("archive" if ARCHIVE.match(page.slug) else "conference" if CONFERENCE.match(page.slug) else None)
        if layout:
            yield page, layout


def build(apply):
    if "layout" not in {col.name for col in connection.introspection.get_table_description(connection.cursor(), Page._meta.db_table)}:
        raise SystemExit("STOP: the Page.layout column is missing. Run `manage.py migrate` first.")
    rows = {"layouts": []}
    skipped = []
    for page, layout in wanted():
        if page.layout != "default":
            skipped.append((page.slug, "its layout is %r already (edited since)" % page.layout))
            continue
        print("%-62s %s" % (page.slug, layout))
        rows["layouts"].append({"slug": page.slug, "old": page.layout, "new": layout})
        if apply:
            Page.objects.filter(pk=page.pk).update(layout=layout)
    for slug, why in skipped:
        print("SKIPPED %s: %s" % (slug, why))
    print("\n%d layout(s) set, %d skipped." % (len(rows["layouts"]), len(skipped)))
    return rows


def undo(rows):
    done = 0
    for entry in rows["layouts"]:
        done += Page.objects.filter(slug=entry["slug"], layout=entry["new"]).update(layout=entry["old"])
    print("restored %d of %d layouts." % (done, len(rows["layouts"])))


run_modes(NAME, build, undo)
