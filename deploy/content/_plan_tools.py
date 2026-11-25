"""Shared helpers of the make_plan.py files of scripts 49 onwards (live page -> plan.json with typed blocks)."""
import hashlib
import html
import json
import re
import subprocess
from urllib.parse import unquote

LANGS = ("uz", "ru", "en")


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(url):
    return json.loads(subprocess.run(["curl", "-s", "--max-time", "90", url], capture_output=True, text=True).stdout)


def menu_labels(section_id):
    """slug -> {lang: label} of the pages (/blog/<section_id>/<slug>) in one menu section."""
    found = {}

    def walk(items):
        for item in items:
            match = re.fullmatch(r"/blog/%d/([^/?#]+)" % section_id, item.get("url") or "")
            if match:
                found[match.group(1)] = item["label"]
            walk(item.get("children", []))

    menu = fetch("https://fermi.uz/api/v1/menu/?page_size=500")
    walk(menu if isinstance(menu, list) else menu.get("results", []))
    return found


def plain(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ").replace("'", "’")
    return re.sub(r"\s+", " ", text).strip()


def media_of(src):
    return unquote(src.split("/media/", 1)[1])


def links_of(fragment):
    """[(href, text)] of the links of an HTML fragment; the pieces of one link split by markup are joined (the same href next to each other)."""
    out = []
    for match in re.finditer(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', fragment, re.S):
        href, text = match.group(1), plain(match.group(2))
        if out and out[-1][0] == href and text:
            out[-1] = (href, (out[-1][1] + " " + text).strip())
        else:
            out.append((href, text))
    return out


def images_of(fragment):
    return [media_of(s) for s in re.findall(r'<img[^>]*\bsrc="([^"]+)"', fragment) if "/media/" in s]


def block(kind, data):
    return {"block_type": kind, "data": data}


def same(value):
    return {lang: value for lang in LANGS}


def image_block(path, alt):
    return block("image", {lang: {"media": path, "alt": alt[lang]} for lang in LANGS})


def document_block(path, caption):
    return block("document", {lang: {"media": path, "caption": caption[lang]} for lang in LANGS})


def page_blocks(slug):
    data = fetch("https://fermi.uz/api/v1/pages/%s/" % slug)["blocks"]
    raw = [b for b in data if b["block_type"] == "raw_html"]
    assert len(raw) == 1 and raw[0]["order"] == 1, slug
    return raw[0], [b for b in data if b["block_type"] == "document"]


def captions_of_cards(documents, captions):
    """existing document cards of the page that get a caption: [{order, document_id, caption{lang}, fp{lang}}]; `captions` is a list of {lang: text} in the order of the cards."""
    assert len(documents) == len(captions), (len(documents), len(captions))
    return [{"order": d["order"], "document_id": d["data"]["uz"]["document_id"], "caption": c,
             "fp": {lang: sha({k: v for k, v in d["data"][lang].items() if k not in ("image", "document")}) for lang in LANGS}}
            for d, c in zip(documents, captions)]


def entry(slug, raw, blocks, cards=None):
    result = {"slug": slug, "order": 1, "fp": {lang: sha(raw["data"][lang]) for lang in LANGS}, "blocks": blocks}
    if cards:
        result["existing_documents"] = cards
    return result


def md_text(fragment):
    """Plain text of an HTML fragment with every link kept as [label](address) (the form LinkifiedText turns back into a link)."""
    def link(match):
        label = plain(match.group(2))
        href = match.group(1).replace(" ", "%20").replace("(", "%28").replace(")", "%29")
        return "[%s](%s)" % (label, href) if label else ""

    return plain(re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', link, fragment, flags=re.S))


def lines_of(fragment):
    """The visible lines of an HTML fragment (a line ends at </p>, </div>, </h1..6>, </li>, <br>, <hr>): [{'text', 'md', 'links', 'images'}]."""
    cut = re.sub(r"<hr\s*/?>|<br\s*/?>", "\n", fragment)
    cut = re.sub(r"</(p|div|h\d|li|tr)>", "\n", cut)
    out = []
    for line in cut.split("\n"):
        text = plain(line)
        if text:
            out.append({"text": text, "md": md_text(line), "links": links_of(line), "images": images_of(line)})
    return out
