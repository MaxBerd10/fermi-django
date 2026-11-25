"""Read-only: compares the pictures of the eight Institut binolari pages in uz / ru / en (live API) and prints the differences as a markdown list."""
import json, re, subprocess
from urllib.parse import unquote, urlsplit
SLUGS = ["rektorat", "oquv-binolari", "2-oquv-kampusi", "vivariy", "simulatsiya-markazi", "kongress-majmuasi", "sport-majmualari", "talabalar-turar-joylari-4"]
def fetch(url): return json.loads(subprocess.run(["curl", "-s", "--max-time", "60", url], capture_output=True, text=True).stdout)
def short(src):
    p = unquote(urlsplit(src).path.split("/media/", 1)[1]); return p.replace("migrated/img/fotogallery/", "")
for s in SLUGS:
    b = fetch(f"https://fermi.uz/api/v1/pages/{s}/")["blocks"][0]["data"]
    srcs = {l: [short(x) for x in re.findall(r'<img[^>]*\bsrc="([^"]+)"', b[l]["html"])] for l in ("uz", "ru", "en")}
    other = {l: re.sub(r"<img[^>]*>|<p>|</p>|<div>|</div>|&nbsp;|\s+", "", b[l]["html"]) for l in ("uz", "ru", "en")}
    print(f"## {s}: uz {len(srcs['uz'])}, ru {len(srcs['ru'])}, en {len(srcs['en'])}", "(text left: %r)" % other if any(other.values()) else "")
    for l in ("ru", "en"):
        missing = [x for x in srcs["uz"] if x not in srcs[l]]; extra = [x for x in srcs[l] if x not in srcs["uz"]]
        dup = [x for x in set(srcs[l]) if srcs[l].count(x) > 1]
        order = srcs[l] != srcs["uz"] and not missing and not extra
        print(f"- {l}: ", "same" if srcs[l] == srcs["uz"] else f"missing {missing} | extra {extra} | duplicates {dup} | only order differs: {order}")
    dup = [x for x in set(srcs["uz"]) if srcs["uz"].count(x) > 1]
    if dup: print("- uz duplicates:", dup)
