"""Export the nine public Institut haqida report pages without writing to Django."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "deploy/content/yillik-hisobot-2026-7/translations.json"
LANGS = {"uz", "ru", "en"}
ORIGIN = "https://fermi.uz"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    options = parser.parse_args()
    if options.output.exists():
        parser.error(f"output already exists: {options.output}")
    slugs = json.loads(TRANSLATIONS.read_text(encoding="utf-8"))
    pages = []
    for slug in slugs:
        url = f"{ORIGIN}/api/v1/pages/{slug}"
        try:
            reply = subprocess.run(
                ["curl", "--fail", "--silent", "--show-error", "--max-time", "20", url],
                check=True,
                capture_output=True,
                text=True,
            )
            page = json.loads(reply.stdout)
        except subprocess.CalledProcessError as error:
            raise SystemExit(f"{slug}: {error.stderr.strip()}") from error
        except json.JSONDecodeError as error:
            raise SystemExit(f"{slug}: the API did not return JSON.") from error
        if page.get("slug") != slug or not isinstance(page.get("blocks"), list) or not page["blocks"]:
            raise SystemExit(f"{slug}: unexpected CMS response.")
        if not all(LANGS <= set(block.get("data", {})) for block in page["blocks"]):
            raise SystemExit(f"{slug}: response lacks one or more raw language payloads.")
        pages.append(page)
        print(f"{slug}: {len(page['blocks'])} blocks")
    with options.output.open("x", encoding="utf-8") as handle:
        json.dump({"origin": ORIGIN, "pages": pages}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Section exported: {options.output}")


if __name__ == "__main__":
    main()
