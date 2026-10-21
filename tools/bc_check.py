# -*- coding: utf-8 -*-
"""Bandcamp 站内搜索：名字 → 同名乐队（第一层，替代 MA）

两条加固（用户 2026-10-21 定）：
1. 结果**每轮落盘带日期快照**（data/snapshots/bc_bands_<date>.json）——接口是站内私有，
   哪天改结构就断，断了还有上一轮顶着。
2. 判定写死：**归一化后完全相等才算占用**（去空格/符号、统一小写）。模糊/相似一律不算。

用法：python3 tools/bc_check.py [--limit N] [--sleep 0.7]
"""
import json, re, time, subprocess, sys, datetime, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAP = DATA / "snapshots"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
URL = "https://bandcamp.com/api/bcsearch_public_api/1/autocomplete_elastic"
TODAY = datetime.date.today().isoformat()

def norm(s: str) -> str:
    """唯一判定口径：去空格、去符号、统一小写"""
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def search(name: str):
    body = json.dumps({"search_text": name, "search_filter": "", "full_page": False, "fan_id": None})
    r = subprocess.run(["curl", "-s", "-m", "25", "-A", UA, "-H", "Content-Type: application/json",
                        "-X", "POST", URL, "-d", body], capture_output=True, text=True)
    txt = (r.stdout or "").strip()
    if not txt.startswith("{"):
        return {"ok": False, "error": (txt[:80] or "empty")}
    try:
        d = json.loads(txt)
    except Exception as e:
        return {"ok": False, "error": f"json: {e}"}
    res = ((d.get("auto") or {}).get("results")) or []
    bands = [x for x in res if x.get("type") == "b"]
    exact = [x for x in bands if norm(x.get("name", "")) == norm(name)]
    return {"ok": True,
            "bands_total": len(bands),
            "exact": len(exact),
            "examples": [{"name": x.get("name"), "url": x.get("item_url_root"),
                          "location": x.get("location"), "tags": (x.get("tag_names") or [])[:3]}
                         for x in exact[:5]],
            "fuzzy_only": [x.get("name") for x in bands[:5]] if not exact else []}

def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    sleep = float(sys.argv[sys.argv.index("--sleep") + 1]) if "--sleep" in sys.argv else 0.7
    pool = json.load(open(DATA / "pool.json", encoding="utf-8"))
    out_path = DATA / "bc_bands.json"
    done = {}
    if out_path.exists():
        done = {x["name"]: x for x in json.load(open(out_path, encoding="utf-8"))}
    todo = [n for n in pool if n not in done or not done[n].get("ok")]
    if limit:
        todo = todo[:limit]
    print(f"todo {len(todo)} / pool {len(pool)}", flush=True)

    for i, name in enumerate(todo, 1):
        rec = {"name": name, "checked_at": TODAY}
        rec.update(search(name))
        done[name] = rec
        flag = "EXACT" if rec.get("exact") else ("-" if rec.get("ok") else "ERR")
        print(f"[{i}/{len(todo)}] {name:24s} {flag:5s} bands={rec.get('bands_total')} "
              f"exact={rec.get('exact')} {rec.get('error','')}", flush=True)
        if i % 10 == 0:
            json.dump(list(done.values()), open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        time.sleep(sleep)

    json.dump(list(done.values()), open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    # 带日期快照（加固 1）
    SNAP.mkdir(exist_ok=True)
    snap = SNAP / f"bc_bands_{TODAY}.json"
    json.dump(list(done.values()), open(snap, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ok = sum(1 for x in done.values() if x.get("ok"))
    exact = sum(1 for x in done.values() if x.get("exact"))
    print(f"\nDONE ok={ok}/{len(done)} exact_names={exact} snapshot={snap}", flush=True)

if __name__ == "__main__":
    main()
