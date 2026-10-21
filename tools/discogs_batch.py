# -*- coding: utf-8 -*-
"""Discogs 精确同名批查（curl 多 URL 连接复用）。只补 done 里没有的名字。"""
import json, subprocess, urllib.parse, re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
D=ROOT/"data"
pool=json.load(open(D/"pool.json",encoding="utf-8"))
outp=D/"discogs.json"
done={x["name"]:x for x in json.load(open(outp,encoding="utf-8"))} if outp.exists() else {}
todo=[n for n in pool if n not in done]
print("todo",len(todo))
if not todo: raise SystemExit
tmp=D/"raw3"; tmp.mkdir(exist_ok=True)
files=[]
CHUNK=150
for start in range(0,len(todo),CHUNK):
    part=todo[start:start+CHUNK]
    args=["curl","-s","-A","metalnamecheck/1.0"]
    for j,n in enumerate(part):
        f=tmp/f"{start+j:03d}.json"
        args += ["https://api.discogs.com/database/search?q="+urllib.parse.quote(n)+"&type=artist&per_page=25","-o",str(f)]
        files.append((n,f))
    subprocess.run(args, check=False)
    print(f"  chunk {start//CHUNK+1}: {len(part)}", flush=True)
def norm(s): return re.sub(r'[^a-z0-9]','',s.lower())
ok=0
for n,f in files:
    try:
        d=json.load(open(f,encoding="utf-8"))
    except Exception:
        continue
    ex=[x for x in d.get("results",[]) if norm(x.get("title",""))==norm(n)]
    done[n]={"name":n,"items":d.get("pagination",{}).get("items",0),"exact":len(ex),"ids":[x.get("id") for x in ex][:5]}
    ok+=1
json.dump(list(done.values()), open(outp,"w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("filled",ok,"total",len(done),"exact names",sum(1 for x in done.values() if x.get("exact")))
