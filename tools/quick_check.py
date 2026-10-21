# -*- coding: utf-8 -*-
import json, time, os, re, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
names=json.load(open("data/pool.json",encoding="utf-8"))
outp="data/quick.json"
done={}
if os.path.exists(outp):
    done={d["name"]:d for d in json.load(open(outp,encoding="utf-8"))}
todo=[n for n in names if n not in done]
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
def slug(n): return re.sub(r'[^a-z0-9]','',n.lower())
def code(url, follow=False):
    class NR(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*a,**k): return None
    op=urllib.request.build_opener() if follow else urllib.request.build_opener(NR)
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    try:
        with op.open(req, timeout=20) as r: return r.status
    except urllib.error.HTTPError as e: return e.code
    except Exception as e: return 0
def probe(n):
    s=slug(n)
    bc=code(f"https://{s}.bandcamp.com/")
    sc=code(f"https://soundcloud.com/{s}")
    dom=code(f"https://rdap.verisign.com/com/v1/domain/{s}.com")
    # 注意：bandcamp 字段不在这里写。urllib 拿到的是 200 Client Challenge 页，判不出空/占，
    # 唯一正确做法是 tools/bc_handle.py（curl -L 看最终 URL）。这里只保留 com / soundcloud。
    return {"name":n,"slug":s,
            "soundcloud":"free" if sc==404 else ("taken" if sc==200 else "unknown"),
            "com":"free" if dom==404 else ("taken" if dom==200 else "unknown"),
            "codes":{"bc":bc,"sc":sc,"rdap":dom}}
print("todo",len(todo),flush=True)
with ThreadPoolExecutor(max_workers=4) as ex:
    for i,rec in enumerate(ex.map(probe,todo),1):
        done[rec["name"]]=rec
        print(f"[{i}/{len(todo)}] {rec['name']} -> com={rec['com']} sc={rec['soundcloud']}",flush=True)
        if i%5==0:
            json.dump(list(done.values()), open(outp,"w",encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(list(done.values()), open(outp,"w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("QUICK DONE",flush=True)
