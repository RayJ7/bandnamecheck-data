# -*- coding: utf-8 -*-
"""曲风名字池生成：16 个曲风（对齐 bandnamemaker 的 sitemap 实际数量），每个约 110 个

每个曲风有自己的词根，不共用金属词库——否则 16 个页是同一批名字换标题。
输出：
  data/genres/<genre>.json  该曲风名字列表
  data/name_genre.json      名字 → 曲风（全局唯一，跨曲风去重）
"""
import json, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
random.seed(20261021)

def norm(s): return re.sub(r'[^a-z0-9]', '', s.lower())

# 结构：每个曲风 = 若干模板 + 词表
G = {
 "rock": dict(
   adj=["Electric","Midnight","Broken","Velvet","Wild","Neon","Rolling","Silver","Burning","Loose","Heavy","Cheap"],
   noun=["Highway","Motel","Riot","Engine","Thunder","Saints","Radio","River","Chrome","Dust","Tattoo","Static"],
   tmpl=["{a} {n}","The {a} {n}"]),
 "punk-rock": dict(
   adj=["Snot","Cheap","Dead","Trash","Rotten","Loud","Broke","Sore","Bad","Raw","Stiff","Nasty"],
   noun=["Kids","City","Noise","Bastards","Choir","Rats","Sleeves","Youth","Cops","Racket","Gutter","Static"],
   tmpl=["The {a} {n}","{a} {n}"]),
 "alt-rock": dict(
   adj=["Slow","Paper","Glass","Quiet","Half","Soft","Grey","Open","Static","Faded","Little","Blank"],
   noun=["Tigers","Machines","Weather","Houses","Shapes","Letters","Rooms","Fever","Ocean","Signal","Wires","Gardens"],
   tmpl=["{a} {n}","{n}","The {a} {n}"]),
 "indie": dict(
   adj=["Little","Modern","Paper","Golden","Hollow","Sunday","Coastal","Northern","Soft","Tiny","Lucky","Slow"],
   noun=["Cinema","Gardens","Postcards","Cousins","Bicycles","Lanterns","Sweaters","Coast","Letters","Coffee","Foxes","Weekend"],
   tmpl=["{a} {n}","The {a} {n}","{n} Club"]),
 "blues": dict(
   adj=["Delta","Bayou","Smoky","Broken","Lowdown","Rusty","Howlin'","Tired","Crossroad","Mojo","Whiskey","Black"],
   noun=["Hound","Train","River","Woman","Blues Band","Shuffle","Bones","Sundown","Holler","Six String","Juke","Gravel"],
   tmpl=["{a} {n}","{a} & The {n}","The {a} {n}"]),
 "country": dict(
   adj=["Dusty","Lonesome","Copper","Dry","Backroad","Hillbilly","Broken","Prairie","Hollow","Whiskey","Ragged","Sunday"],
   noun=["Boots","Creek","Chaparral","Ranch","Rose","Truck","Chapel","Mesa","Hymn","Firewood","Saddle","Gospel"],
   tmpl=["{a} {n}","The {a} {n}","{n} Brothers"]),
 "folk-acoustic": dict(
   adj=["Green","Willow","Quiet","Winter","Wandering","Gentle","Hollow","Harvest","Mossy","Pale","Wandering","Old"],
   noun=["Pines","River","Meadow","Hymn","Sparrow","Harbor","Linen","Orchard","Stone","Lullaby","Valley","Bell"],
   tmpl=["{a} {n}","The {a} {n}","{n} & Oak"]),
 "jazz": dict(
   adj=["Blue","Late","Velvet","Smoke","Midnight","Quiet","Crooked","Silver","Uptown","Amber","Low","Cool"],
   noun=["Quartet","Trio","Room","Standard","Noir","Swing","Avenue","Session","Combo","Boptet","Lounge","Horn"],
   tmpl=["The {a} {n}","{a} {n}","{n} Collective"]),
 "latin": dict(
   adj=["Sol","Luna","Fuego","Rosa","Negro","Alma","Cielo","Tierra","Viejo","Nuevo","Cobre","Sal"],
   noun=["Brujo","Corazón","Ritmo","Camino","Fuego","Mar","Cumbia","Son","Barrio","Tambor","Llama","Río"],
   tmpl=["{a} {n}","{n} de {a}"]),
 "reggae": dict(
   adj=["Roots","Rasta","Irie","Dub","Island","Sunny","Heavy","Jah","Cool","Rockers","Burning","One"],
   noun=["Lion","Dub","Sound","Corner","River","Yard","Chant","Vibration","Foundation","Fire","Kingston","Zion"],
   tmpl=["{a} {n}","The {a} {n}","{n} Sound System"]),
 "funk": dict(
   adj=["Hot","Greasy","Super","Sticky","Rubber","Electric","Loose","Funky","Slippery","Bad","Sweet","Nasty"],
   noun=["Groove","Machine","Bone","Rocket","Thumper","Sister","Rebel","Juice","Engine","Strut","Monster","Grease"],
   tmpl=["{a} {n}","The {a} {n}","{n} Revue"]),
 "hip-hop": dict(
   adj=["Lil","Young","Big","Kold","Iron","Gold","Mad","Slim","Rogue","Slick","Bronze","Ghost"],
   noun=["Prophet","Cipher","Static","Crown","Verse","Ronin","Alley","Syndicate","Motive","Arsenal","Bishop","Riot"],
   tmpl=["{a} {n}","{a}{n}"]),
 "pop": dict(
   adj=["Neon","Sugar","Silver","Bright","Honey","Candy","Golden","Electric","Little","Super","Velvet","Disco"],
   noun=["Hearts","Summer","Lights","Dream","Rush","Bubble","Star","Kiss","Motion","Glitter","Avenue","Beat"],
   tmpl=["{a} {n}","{n}","The {a} {n}"]),
 "electronica": dict(
   adj=["Neon","Laser","Urban","Nano","Chrome","Digital","Pulse","Static","Prism","Vapour","Hyper","Wire"],
   noun=["Signal","Circuit","Matrix","Nightdrive","Frequency","Protocol","Vector","Grid","Sequence","Rave","Cascade","Terminal"],
   tmpl=["{a} {n}","{n}","{a}{n}"]),
 "r-and-b-soul": dict(
   adj=["Velvet","Silk","Honey","Late","Smooth","Golden","Slow","Amber","Warm","Soft","Blue","Sunday"],
   noun=["Soul","Touch","Room","Lover","Groove","Whisper","Motion","Velour","Sunday","Pleasure","Rose","Afterhours"],
   tmpl=["{a} {n}","The {a} {n}","{n}"]),
 "heavy-metal": dict(   # 首页那批的曲风标签；不与 metal 重复生成
   adj=[], noun=[], tmpl=[]),
}

def gen(genre, cfg, want=110):
    out = set()
    adj, nouns, tmpls = cfg["adj"], cfg["noun"], cfg["tmpl"]
    for t in tmpls:
        for a in adj:
            for n in nouns:
                s = t.format(a=a, n=n)
                words = [w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúñÑ']+", s)]
                if len(set(words)) < len(words):      # 「Fuego Fuego」这种同词重复不要
                    continue
                if 6 <= len(s) <= 26:
                    out.add(s)
    pool = sorted(out)
    random.shuffle(pool)
    return pool[:want]

def main():
    (D / "genres").mkdir(exist_ok=True)
    metal = json.load(open(D / "metal.json", encoding="utf-8"))
    mapping = {n: "metal" for n in metal}
    total = len(metal)
    for g, cfg in G.items():
        if g in ("heavy-metal",):
            continue
        names = gen(g, cfg)
        keep = []
        for n in names:
            if norm(n) in {norm(x) for x in mapping}:
                continue
            keep.append(n)
        for n in keep:
            mapping[n] = g
        json.dump(keep, open(D / "genres" / f"{g}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"{g:16s} {len(keep)}")
        total += len(keep)
    json.dump(mapping, open(D / "name_genre.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(sorted(mapping.keys()), open(D / "pool.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("total names", total, "| unique", len(mapping))

if __name__ == "__main__":
    main()
