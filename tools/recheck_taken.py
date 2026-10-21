# -*- coding: utf-8 -*-
"""复核所有判为 taken 的 Bandcamp handle（一条一条真开，浏览器判）

2026-10-21 抽检 20 条发现 1 条假 taken（Basalt Lantern 实际是注册页）。
规则：最终 URL 含 signup?new_domain= → 空；停在 <slug>.bandcamp.com → 有人；
      标题含 Client Challenge → 被挑战，重试两次后仍如此就写 unknown（不写 taken）。
"""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parent.parent / "data"
p = D / "quick.json"
q = json.load(open(p, encoding="utf-8"))
todo = [x for x in q if x.get("bandcamp") == "taken"]
print("recheck", len(todo), flush=True)

def save():
    json.dump(q, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(locale="en-US",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"})
    pg = ctx.new_page()
    flipped = 0
    for i, x in enumerate(todo, 1):
        url = f"https://{x['slug']}.bandcamp.com/"
        verdict = "unknown"
        final = ""
        for attempt in range(3):
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=35000)
                pg.wait_for_timeout(1200)
                final = pg.url
                title = pg.title() or ""
                if "signup?new_domain" in final:
                    verdict = "free"; break
                if "Client Challenge" in title or title.strip() == "":
                    verdict = "unknown"; time.sleep(2.5); continue
                if final.startswith(f"https://{x['slug']}.bandcamp.com"):
                    verdict = "taken"; break
                verdict = "unknown"; break
            except Exception as e:
                verdict = "unknown"; time.sleep(1.5)
        if verdict != "taken":
            flipped += 1
        x["bandcamp"] = verdict
        x["bc_final"] = final[:90]
        if i % 10 == 0:
            save()
        print(f"[{i}/{len(todo)}] {x['name']:24s} -> {verdict:7s} {final[:56]}", flush=True)
    save()
    b.close()
print("FLIPPED(非 taken)", flipped, flush=True)
from collections import Counter
print(Counter(x.get("bandcamp") for x in q), flush=True)
