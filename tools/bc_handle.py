# -*- coding: utf-8 -*-
"""Bandcamp handle 批查（串行 curl，唯一可靠的判法）

2026-10-21 实测结论：
- `--parallel` 会触发 Bandcamp 的 Client Challenge，挑战页就挂在 <slug>.bandcamp.com 上，
  看着像「已占」——一次能造出上千条假 taken。**并行不可用**。
- 串行 + 跟随跳转：最终 URL 含 signup?new_domain= 才是空，否则已占。
- 分块 120，每块落盘；每块做完瓦查 taken 比例，>85% 就逐条复核一遍（防再次被挑战页骗）。
"""
import json, subprocess, time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
p = D / "quick.json"
q = json.load(open(p, encoding="utf-8"))
todo = [x for x in q if x.get("bandcamp") in (None, "unknown")]
print("todo", len(todo), flush=True)
if not todo:
    raise SystemExit

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
CHUNK = 120

def save():
    json.dump(q, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

def judge(x, final):
    if not final:
        return "unknown"
    if "signup?new_domain" in final:
        return "free"
    if final.startswith(f"https://{x['slug']}.bandcamp.com"):
        return "taken"
    return "unknown"

for start in range(0, len(todo), CHUNK):
    part = todo[start:start + CHUNK]
    args = ["curl", "-s", "-L", "-A", UA, "-w", "%{url_effective}\n"]
    for x in part:
        args += [f"https://{x['slug']}.bandcamp.com/", "-o", "/dev/null"]
    r = subprocess.run(args, capture_output=True, text=True, timeout=1200)
    lines = [l.strip() for l in r.stdout.split("\n") if l.strip()]
    if len(lines) != len(part):
        lines = []
        for x in part:
            rr = subprocess.run(["curl", "-s", "-L", "-A", UA, "-w", "%{url_effective}",
                                 "-o", "/dev/null", f"https://{x['slug']}.bandcamp.com/"],
                                capture_output=True, text=True)
            lines.append(rr.stdout.strip())
            time.sleep(0.4)
    for x, f in zip(part, lines):
        x["bandcamp"] = judge(x, f)
        x["bc_final"] = f[:90]
    taken_ratio = sum(1 for x in part if x["bandcamp"] == "taken") / max(1, len(part))
    if taken_ratio > 0.85:
        print(f"  !! chunk {start//CHUNK+1} taken 比例 {taken_ratio:.0%}，逐条复核", flush=True)
        for x in part:
            if x["bandcamp"] != "taken":
                continue
            time.sleep(0.5)
            rr = subprocess.run(["curl", "-s", "-L", "-A", UA, "-w", "%{url_effective}",
                                 "-o", "/dev/null", f"https://{x['slug']}.bandcamp.com/"],
                                capture_output=True, text=True)
            x["bandcamp"] = judge(x, rr.stdout.strip())
            x["bc_final"] = rr.stdout.strip()[:90]
    save()
    print(f"  chunk {start//CHUNK+1}: {len(part)} 条已落盘", flush=True)

print(Counter(x.get("bandcamp") for x in q), flush=True)
print("DONE", flush=True)
