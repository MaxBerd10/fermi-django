"""Alignment of the blocks of two languages of one old page (Needleman-Wunsch on a similarity of type, numbers, links and length). Used to write by hand the pages whose three languages differ
in structure: `align(uz_specs, other_specs)` -> list of (i or None, j or None)."""
import re


def tokens(spec):
    text = spec.get("text") or spec.get("caption") or " ".join(spec.get("items", [])) or " ".join(spec.get("headers", []) + [c for r in spec.get("rows", []) for c in r]) or spec.get("media", "") or spec.get("src", "")
    return text


def nums(text):
    return set(re.findall(r"\d{2,}", text))


def urls(text):
    return set(re.findall(r"\]\(([^)]+)\)", text)) | set(re.findall(r"https?://\S+", text))


def norm(media):
    """The file name of a picture without its folder, the case and every sign: the same picture is saved with different apostrophes in the names."""
    return re.sub(r"[^0-9a-zа-я]", "", (media or "").rsplit("/", 1)[-1].lower())


def score(a, b, pos=0.0):
    ta, tb = tokens(a), tokens(b)
    s = 0.0
    kinds = {a["t"], b["t"]}
    if a["t"] == b["t"]:
        s += 1.0
    elif kinds <= {"heading", "paragraph"}:
        s += 0.6
    elif kinds <= {"list", "paragraph"}:
        s += 0.2
    else:
        s -= 1.5
    na, nb = nums(ta), nums(tb)
    if na or nb:
        s += 2.0 * len(na & nb) / max(1, len(na | nb))
    ua, ub = urls(ta), urls(tb)
    if ua or ub:
        s += 3.0 * len(ua & ub) / max(1, len(ua | ub))
    if a["t"] in ("image", "document"):
        s += 3.0 if norm(a.get("media")) == norm(b.get("media")) else -1.0
    la, lb = max(len(ta), 1), max(len(tb), 1)
    s += 1.0 * min(la, lb) / max(la, lb)
    s += 0.9 * max(0.0, 1.0 - 4.0 * pos)  # blocks of the same place of the page
    return s


def align(a, b, gap=-0.9, floor=1.2):
    n, m = len(a), len(b)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap
        back[i][0] = "u"
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap
        back[0][j] = "l"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sc = score(a[i - 1], b[j - 1], abs((i - 1) / max(n, 1) - (j - 1) / max(m, 1)))
            best, move = dp[i - 1][j] + gap, "u"
            if dp[i][j - 1] + gap > best:
                best, move = dp[i][j - 1] + gap, "l"
            if sc >= floor and dp[i - 1][j - 1] + sc > best:
                best, move = dp[i - 1][j - 1] + sc, "d"
            dp[i][j], back[i][j] = best, move
    out, i, j = [], n, m
    while i > 0 or j > 0:
        mv = back[i][j]
        if mv == "d":
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif mv == "u":
            out.append((i - 1, None)); i -= 1
        else:
            out.append((None, j - 1)); j -= 1
    return out[::-1]
