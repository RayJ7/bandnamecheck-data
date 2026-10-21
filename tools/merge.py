# -*- coding: utf-8 -*-
"""合并四层核验结果（Bandcamp 站内搜索为第一层；MA 降级为可选加分层）

口径（用户 2026-10-21 定）：
- 可滚（rollable）= 四层全部有结果：.com / Bandcamp handle / SoundCloud / Bandcamp 同名搜索 / Discogs
- 全空（free）    = 四层全空，且 Bandcamp 无同名艺人（归一化完全相等才算）
- 已占（taken）   = Bandcamp 精确同名 >0 或 Discogs 精确同名 >0（MA 有结果时也算）
- 归一化判定写死在 bc_check.py：去空格去符号统一小写后完全相等，模糊一律不算
"""
import json, datetime, re
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "data"
TODAY = datetime.date.today().isoformat()

names = json.load(open(D / "pool.json", encoding="utf-8"))
quick = {x["name"]: x for x in json.load(open(D / "quick.json", encoding="utf-8"))}
bc = {x["name"]: x for x in json.load(open(D / "bc_bands.json", encoding="utf-8"))} if (D / "bc_bands.json").exists() else {}
dg = {x["name"]: x for x in json.load(open(D / "discogs.json", encoding="utf-8"))}
ma = {x["name"]: x for x in json.load(open(D / "ma2.json", encoding="utf-8"))} if (D / "ma2.json").exists() else {}

out = []
for n in names:
    q, b, d, m = quick.get(n, {}), bc.get(n, {}), dg.get(n, {}), ma.get(n, {})
    out.append({
        "name": n,
        "slug": q.get("slug") or re.sub(r'[^a-z0-9]', '', n.lower()),
        "com": q.get("com", "unknown"),
        "bandcamp": q.get("bandcamp", "unknown"),
        "soundcloud": q.get("soundcloud", "unknown"),
        "bc": {"ok": bool(b.get("ok")), "bands_total": b.get("bands_total"),
               "exact": b.get("exact", 0), "examples": b.get("examples") or [],
               "fuzzy_only": b.get("fuzzy_only") or [], "error": b.get("error")},
        "discogs": {"items": d.get("items", 0), "exact": d.get("exact", 0)},
        "ma": {"status": m.get("status", "unchecked"), "exact": m.get("exact", 0),
               "bands": m.get("bands") or [], "total": m.get("total", 0)},
        "checked_at": TODAY,
    })

def rollable(x):
    return (x["com"] in ("free", "taken") and x["bandcamp"] in ("free", "taken")
            and x["soundcloud"] in ("free", "taken") and x["bc"]["ok"])

def taken(x):
    # 与 build.py 同口径：handle 被注册也算已占（用户 2026-10-21 命门规则）
    return (x["bc"]["exact"] > 0 or x["discogs"]["exact"] > 0 or x["ma"]["exact"] > 0
            or x["bandcamp"] == "taken")

def free(x):
    return (rollable(x) and x["com"] == "free" and x["bandcamp"] == "free"
            and x["soundcloud"] == "free" and x["bc"]["exact"] == 0 and x["discogs"]["exact"] == 0)

json.dump(out, open(D / "names.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

R = [x for x in out if rollable(x)]
print(f"merged={len(out)} rollable={len(R)} free={sum(1 for x in R if free(x))} "
      f"taken={sum(1 for x in R if taken(x))} held={len(out) - len(R)}")
print("  bc exact:", sum(1 for x in out if x["bc"]["exact"] > 0),
      "| discogs exact:", sum(1 for x in out if x["discogs"]["exact"] > 0),
      "| ma exact:", sum(1 for x in out if x["ma"]["exact"] > 0),
      "| bc error:", sum(1 for x in out if not x["bc"]["ok"]))
