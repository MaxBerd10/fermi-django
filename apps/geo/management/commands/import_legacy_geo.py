"""
Imports Uzbekistan's region/district/quarter hierarchy and the
connect-leaders list from the old site's live public API -- used by the
Qabul (admission) and Virtual qabulxona (contact) forms' cascading address
dropdowns, which are otherwise stuck empty (there was no Django model for
any of this before).

Like regions/districts/quarters themselves, names come back Uzbek-only
regardless of ?lang= (the old API ignores it here) -- see
frontend/src/lib/regionNames.ts's own note on this for regions; districts
and quarters are shown in Uzbek only throughout the app, matching that.

Idempotent: re-running clears and rebuilds every row, same as the other
legacy importers. Fetches one page per district for quarters (~200 calls)
so a full run takes a few minutes.

Usage:
    python manage.py import_legacy_geo --dry-run
    python manage.py import_legacy_geo
"""
from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request

import certifi
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.geo.models import ConnectLeader, District, Quarter, Region

_API_BASE = "https://api.fermi.uz/v1"
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_json(path: str, **params) -> list:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{_API_BASE}{path}{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "fermi-django-migration/0.1"})
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CONTEXT) as resp:
        return json.load(resp)["data"]


class Command(BaseCommand):
    help = "Import regions/districts/quarters and connect-leaders from the old site's live API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and report only -- writes nothing."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        regions = _get_json("/regions")
        leaders = _get_json("/connect-leaders")
        self.stdout.write(f"{len(regions)} region(s), {len(leaders)} connect-leader(s) to process.\n")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run -- not fetching districts/quarters (would take a while)."))
            return

        with transaction.atomic():
            Quarter.objects.all().delete()
            District.objects.all().delete()
            Region.objects.all().delete()
            ConnectLeader.objects.all().delete()

            for leader_order, leader in enumerate(leaders):
                ConnectLeader.objects.create(name=leader["name"], order=leader_order)

            district_count = 0
            quarter_count = 0
            for region_order, region_data in enumerate(regions):
                region = Region.objects.create(name=region_data["name"], order=region_order)
                districts = _get_json("/districts", regionId=region_data["id"])
                for district_order, district_data in enumerate(districts):
                    district = District.objects.create(
                        region=region, name=district_data["name"], order=district_order
                    )
                    district_count += 1
                    quarters = _get_json("/quarters", districtId=district_data["id"])
                    for quarter_order, quarter_data in enumerate(quarters):
                        Quarter.objects.create(
                            district=district, name=quarter_data["name"], order=quarter_order
                        )
                        quarter_count += 1
                self.stdout.write(f"  {region.name}: {len(districts)} district(s)")

        self.stdout.write(self.style.SUCCESS(
            f"\nImported {len(regions)} region(s), {district_count} district(s), "
            f"{quarter_count} quarter(s), {len(leaders)} connect-leader(s)."
        ))
