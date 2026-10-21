# -*- coding: utf-8 -*-
"""多页构建：16 个曲风页（首页 = metal），每页自己的名字池与核验记录"""
import json, html, datetime, shutil
from pathlib import Path

ROOT = Path(__file__).parent
PUB = ROOT / "dist"
SRC = ROOT / "public"
DATA = ROOT / "data"
BUILD = datetime.date.today().isoformat()
GA = "G-5STK2RPWNR"
SITE = "https://bandnamecheck.com"

# key, label, slug, keyword
GENRES = [
    ("metal", "Metal", "/", "metal band name generator"),
    ("rock", "Rock", "/rock-band-name-generator", "rock band name generator"),
    ("punk-rock", "Punk", "/punk-band-name-generator", "punk band name generator"),
    ("alt-rock", "Alt-Rock", "/alt-rock-band-name-generator", "alt rock band name generator"),
    ("indie", "Indie", "/indie-band-name-generator", "indie band name generator"),
    ("blues", "Blues", "/blues-band-name-generator", "blues band name generator"),
    ("country", "Country", "/country-band-name-generator", "country band name generator"),
    ("folk-acoustic", "Folk", "/folk-band-name-generator", "folk band name generator"),
    ("jazz", "Jazz", "/jazz-band-name-generator", "jazz band name generator"),
    ("latin", "Latin", "/latin-band-name-generator", "latin band name generator"),
    ("reggae", "Reggae", "/reggae-band-name-generator", "reggae band name generator"),
    ("funk", "Funk", "/funk-band-name-generator", "funk band name generator"),
    ("hip-hop", "Hip-Hop", "/hip-hop-band-name-generator", "hip hop band name generator"),
    ("pop", "Pop", "/pop-band-name-generator", "pop band name generator"),
    ("electronica", "Electronic", "/electronic-band-name-generator", "electronic band name generator"),
    ("r-and-b-soul", "R&B", "/r-and-b-band-name-generator", "r&b band name generator"),
]

all_names = json.load(open(DATA / "names.json", encoding="utf-8"))
COPY = json.load(open(DATA / "genre_copy.json", encoding="utf-8"))
genre_of = json.load(open(DATA / "name_genre.json", encoding="utf-8"))

def gname(n):
    return genre_of.get(n["name"], "metal")

def bc_ok(n):
    return bool((n.get("bc") or {}).get("ok"))

def has_hit(n):
    """TAKEN 的判据（用户 2026-10-21 定的命门口径）：
    要么已有同名艺人，要么 Bandcamp handle 已经被注册。
    只报 "0 同名" 却把 handle 已被人用的名字标成 OPEN，等于让人拿去注册再发现被占。"""
    return ((n.get("bc") or {}).get("exact", 0) > 0 or (n.get("discogs") or {}).get("exact", 0) > 0
            or (n.get("ma") or {}).get("exact", 0) > 0 or n.get("bandcamp") == "taken")

def full_record(n):
    return (n.get("com") in ("free", "taken") and n.get("bandcamp") in ("free", "taken")
            and n.get("soundcloud") in ("free", "taken") and bc_ok(n))

def free_all(n):
    return (full_record(n) and n.get("com") == "free" and n.get("bandcamp") == "free"
            and n.get("soundcloud") == "free" and (n.get("bc") or {}).get("exact", 0) == 0
            and (n.get("discogs") or {}).get("exact", 0) == 0)

def chip(ok, text):
    return f'<span class="chk {"ok" if ok else "no"}">{html.escape(text)}</span>'

def card(n):
    bc, dg = n.get("bc") or {}, n.get("discogs") or {}
    free_flag = free_all(n)
    state = "TAKEN" if has_hit(n) else ("OPEN" if bc_ok(n) else "HELD")
    rows = [
        chip(n.get("com") == "free", f".com {'free' if n.get('com') == 'free' else 'taken'}"),
        chip(n.get("bandcamp") == "free", f"bandcamp handle {'free' if n.get('bandcamp') == 'free' else 'taken'}"),
        chip(n.get("soundcloud") == "free", f"soundcloud {'free' if n.get('soundcloud') == 'free' else 'taken'}"),
    ]
    if bc_ok(n):
        rows.append(chip(bc.get("exact", 0) == 0, f"bandcamp {bc.get('exact', 0)} same-name"))
    else:
        rows.append('<span class="chk na">bandcamp not checked</span>')
    if dg.get("exact", 0) > 0:
        rows.append(chip(False, f"discogs {dg['exact']} same-name"))
    elif dg:
        rows.append(chip(True, "discogs 0 same-name"))
    return (f'<article class="card{" is-free" if free_flag else ""}{" is-partly" if state == "HELD" else ""}" data-name="{html.escape(n["name"])}">'
            f'<div class="card-top"><h3>{html.escape(n["name"])}</h3><span class="stamp">{state}</span></div>'
            f'<div class="checks">{"".join(rows)}</div>'
            f'<button class="copy" type="button">copy name</button></article>')

def who(n):
    out = []
    for ex in (n.get("bc") or {}).get("examples", [])[:1]:
        label = html.escape(ex.get("name") or "")
        if ex.get("url"):
            label = f'<a href="{html.escape(ex["url"])}" rel="nofollow noopener" target="_blank">{label}</a>'
        tags = ", ".join((ex.get("tags") or [])[:2])
        loc = f' · {html.escape(ex.get("location"))}' if ex.get("location") else ""
        out.append(f'{label}<span class="dim"> · {html.escape(tags)}{loc}</span>')
    for band in (n.get("ma") or {}).get("bands", [])[:1]:
        label = html.escape(band.get("band") or "")
        if band.get("url"):
            label = f'<a href="{html.escape(band["url"])}" rel="nofollow noopener" target="_blank">{label}</a>'
        out.append(f'{label}<span class="dim"> · MA · {html.escape(band.get("genre") or "")}</span>')
    return "<br>".join(out) if out else "—"

TPL = (ROOT / "template.html").read_text(encoding="utf-8")

MIN_ROLLABLE = 30

def genre_rows(key):
    ns = [n for n in all_names if gname(n) == key]
    roll = [n for n in ns if full_record(n)]
    return ns, roll

LIVE = []
for k, label, slug, kw in GENRES:
    ns, roll = genre_rows(k)
    if len(roll) >= MIN_ROLLABLE:
        LIVE.append((k, label, slug, kw))
print("live pages:", [x[0] for x in LIVE])

NAV_ALL = "".join(
    f'<li><a href="{slug}">{label}</a></li>' for k, label, slug, kw in LIVE if k != "metal"
)

def rows_for(taken):
    return "".join(
        f'<tr><td class="nm">{html.escape(n["name"])}</td>'
        f'<td class="num">{(n.get("bc") or {}).get("exact", 0) or "—"}</td>'
        f'<td class="num">{(n.get("discogs") or {}).get("exact", 0) or "—"}</td>'
        f'<td class="num">{(n.get("ma") or {}).get("exact", 0) or "—"}</td>'
        f'<td class="who">{who(n)}</td></tr>'
        for n in taken[:10])

PUB.mkdir(exist_ok=True)
(DATA / "genres").exists() and (PUB / "data").mkdir(exist_ok=True)
for f in ("style.css", "app.js", "favicon.svg"):
    if (SRC / f).exists():
        shutil.copy(SRC / f, PUB / f)

summary = []
urls = []
for key, label, slug, kw in LIVE:
    names = [n for n in all_names if gname(n) == key]
    rollable = [n for n in names if full_record(n)]
    free = [n for n in rollable if free_all(n)]
    taken = [n for n in rollable if has_hit(n)]
    taken.sort(key=lambda n: (-((n.get("bc") or {}).get("exact") or 0), n["name"]))
    checked = max([n.get("checked_at", BUILD) for n in names], default=BUILD)

    cp = COPY.get(key, {})
    pool_set = {n["name"] for n in names}
    missing = [x["name"] for x in cp.get("picks", []) if x["name"] not in pool_set]
    if missing:
        print(f"  !! {key} 举例不在池里: {missing}")
    picks_html = "".join(
        f'<div class="pick"><h3>{html.escape(p["name"])}</h3><p>{html.escape(p["why"])}</p></div>'
        for p in cp.get("picks", []))
    paras_html = "".join(f"<p>{html.escape(x)}</p>" for x in cp.get("paras", []))
    copy_block = (f'<section class="howto"><h2>How {label} band names are built</h2>'
                  f'<div class="prose">{paras_html}</div>'
                  f'<div class="picks">{picks_html}</div></section>') if cp else ""

    title = f"{label} Band Name Generator — Every Name Checked"
    desc = (f"Roll ten {kw.split(' band name')[0]} band names. Each one arrives with its own record: "
            f".com, Bandcamp and SoundCloud handles, plus a same-name search on Bandcamp — exact matches only.")
    h1 = f"{label} band name <em>generator</em>"

    out = (TPL
           .replace("{{GA_ID}}", GA)
           .replace("{{TITLE}}", html.escape(title))
           .replace("{{DESC}}", html.escape(desc))
           .replace("{{CANONICAL}}", SITE + slug)
           .replace("{{H1}}", h1)
           .replace("{{GENRE}}", label)
           .replace("{{CHECKED}}", checked)
           .replace("{{SHOWN}}", str(len(rollable)))
           .replace("{{FREE}}", str(len(free)))
           .replace("{{TAKEN}}", str(len(taken)))
           .replace("{{DATA_SRC}}", "/data/" + key + ".json")
           .replace("{{CARDS}}", "\n".join(card(n) for n in (free[:4] if free else rollable[:4])))
           .replace("{{TAKEN_ROWS}}", rows_for(taken))
           .replace("{{FREE_LIST}}", "".join(f"<li>{html.escape(n['name'])}</li>" for n in free[:15]))
           .replace("{{NAV}}", NAV_ALL)
           .replace("{{GENRE_COPY}}", copy_block))
    out = "\n".join(l.lstrip() for l in out.splitlines())

    if slug == "/":
        path = PUB / "index.html"
    else:
        path = PUB / slug.strip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out, encoding="utf-8")
    b = path.read_bytes().replace(bytes([13, 13, 10]), bytes([10])).replace(bytes([13, 10]), bytes([10]))
    path.write_bytes(b)

    slim = [{"name": n["name"], "com": n["com"], "bandcamp": n["bandcamp"], "soundcloud": n["soundcloud"],
             "bc": {"ok": n["bc"]["ok"], "exact": n["bc"]["exact"]},
             "discogs": {"exact": n["discogs"]["exact"]},
             "ma": {"exact": n["ma"]["exact"]}} for n in rollable]
    (PUB / "data" / f"{key}.json").write_text(json.dumps(slim, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    urls.append(slug)
    summary.append((key, len(rollable), len(free), len(taken), len(names) - len(rollable)))

# 首页的 /data/metal.json 保持旧路径兼容（app.js 读 body data-src，已参数化）
(PUB / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: https://bandnamecheck.com/sitemap.xml\n", encoding="utf-8")
(PUB / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f'  <url><loc>{SITE}{u if u != "/" else "/"}</loc><lastmod>{BUILD}</lastmod>'
              f'<changefreq>weekly</changefreq><priority>{"1.0" if u == "/" else "0.8"}</priority></url>\n' for u in urls)
    + "</urlset>\n", encoding="utf-8")

print("genre            rollable free taken held")
for key, r, f, t, h in summary:
    print(f"{key:16s} {r:8d} {f:4d} {t:5d} {h:5d}")
print("TOTAL rollable", sum(s[1] for s in summary), "free", sum(s[2] for s in summary),
      "taken", sum(s[3] for s in summary), "| pages", len(urls))
