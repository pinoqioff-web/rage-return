import os,json,re,random,subprocess,urllib.request,time

ROOT="assets/quran"
API="https://mp3quran.net/api/v3"

THEMES={
"rizq":["11:6","17:30","28:77","34:36","51:58","65:2-3"],
"work":["9:105","62:10","67:15","73:20"],
"dua":["2:186","3:8","21:87","40:60"],
"parents":["17:23-24","31:14","46:15"],
"marriage":["24:32","30:21"],
"family":["25:74","64:14-15","66:6"],
"patience":["2:153","2:155-157","3:200","39:10"],
"sadness":["12:84-86","94:5-6"],
"anxiety":["3:173","8:30","9:40","13:28"],
"tranquility":["13:28","48:4","9:26"],
"hope":["12:87","39:53","94:5-6"],
"repentance":["4:17","25:70","66:8"],
"sins":["4:31","53:32","24:19"],
"gratitude":["14:7","2:152","31:12"],
"guidance":["1:6-7","2:2","17:9"],
"justice":["4:135","5:8","16:90"],
"death":["3:185","21:35","29:57"],
"grave":["23:99-100","82:4-5"],
"resurrection":["22:7","36:51-52","75:3-4"],
"judgement":["99:6-8","101:6-11","69:19-37","84:7-12"],
"heaven":["3:133-136","9:72","76:11-22"],
"hell":["4:56","67:6-11","78:21-30"],
"afterlife":["57:20","87:16-17","28:77"]
}

os.makedirs(ROOT,exist_ok=True)

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"PINOQIO-Quran/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

# reciters
data=get(API+"/reciters?language=ar")
reciters=data.get("reciters",[])

# استبعاد القراء الذين طلبت استبعادهم
skip_names=("عبدالرحمن مسعد","عبد الرحمن مسعد","إسلام صبحي","اسلام صبحي")

# التوقيتات المتاحة
timing=get(API+"/ayat_timing/reads")
timing_ids={int(x["id"]) for x in timing if "id" in x}

# نحاول مطابقة read/moshaf مع بيانات القارئ
choices=[]
for r in reciters:
    name=(r.get("name") or "").strip()
    if any(x in name for x in skip_names):
        continue

    for m in r.get("moshaf",[]):
        rid=m.get("id")
        server=m.get("server")
        suras=m.get("surah_list","")
        if not rid or not server:
            continue
        if int(rid) not in timing_ids:
            continue
        choices.append({
            "id":int(rid),
            "name":name,
            "server":server.rstrip("/")+"/",
            "suras":set(int(x) for x in str(suras).split(",") if x.isdigit())
        })

print("قراء لديهم توقيت آيات:",len(choices))

# منع تكرار القارئ
used_reciters=set()
downloaded=0

def parse_ref(ref):
    s,a=ref.split(":")
    if "-" in a:
        x,y=map(int,a.split("-"))
    else:
        x=y=int(a)
    return int(s),x,y

for theme,refs in THEMES.items():
    outdir=os.path.join(ROOT,theme)
    os.makedirs(outdir,exist_ok=True)

    # لو التصنيف فيه ملف بالفعل نتركه
    existing=[
        x for x in os.listdir(outdir)
        if x.lower().endswith(".mp3")
    ]
    if existing:
        print("SKIP",theme,"(موجود)")
        continue

    random.shuffle(refs)

    made=False
    for ref in refs:
        sura,a1,a2=parse_ref(ref)

        pool=[
            x for x in choices
            if x["id"] not in used_reciters and sura in x["suras"]
        ]
        random.shuffle(pool)

        for rec in pool[:12]:
            try:
                timing_url=f"{API}/ayat_timing?surah={sura}&read={rec['id']}"
                arr=get(timing_url)

                wanted=[]
                for x in arr:
                    ay=x.get("ayah")
                    if isinstance(ay,int) and a1 <= ay <= a2:
                        wanted.append(x)

                if not wanted:
                    continue

                start=min(x["start_time"] for x in wanted)/1000
                end=max(x["end_time"] for x in wanted)/1000
                duration=end-start

                if duration<=0 or duration>60:
                    continue

                # اسم الملف آمن
                safe=re.sub(r"[^A-Za-z0-9_-]+","_",rec["name"]).strip("_")
                outfile=os.path.join(outdir,
                    f"{safe}__{theme}__{sura}-{a1}-{a2}.mp3")

                if os.path.exists(outfile):
                    used_reciters.add(rec["id"])
                    made=True
                    break

                # ملف السورة
                src=rec["server"]+f"{sura:03d}.mp3"
                tmp=os.path.join(ROOT,f".tmp_{rec['id']}_{sura}.mp3")

                print(f"DOWN {theme}: {rec['name']} | {ref} | {duration:.1f}s")

                subprocess.run([
                    "curl","-L","--fail","--silent","--show-error",
                    "-o",tmp,src
                ],check=True)

                subprocess.run([
                    "ffmpeg","-hide_banner","-loglevel","error",
                    "-ss",str(start),
                    "-to",str(end),
                    "-i",tmp,
                    "-vn","-acodec","libmp3lame","-q:a","4",
                    outfile
                ],check=True)

                os.remove(tmp)

                used_reciters.add(rec["id"])
                downloaded+=1
                made=True
                break

            except Exception as e:
                print("ERR:",theme,rec["name"],str(e)[:120])
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except:
                    pass

        if made:
            break

    if not made:
        print("NO CLIP:",theme)

# إعادة بناء index
files=[]
for theme in THEMES:
    d=os.path.join(ROOT,theme)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.lower().endswith(".mp3"):
            files.append({
                "file":f"/assets/quran/{theme}/{f}",
                "theme":theme
            })

with open(os.path.join(ROOT,"index.json"),"w",encoding="utf-8") as f:
    json.dump(files,f,ensure_ascii=False,indent=2)

print()
print("================================")
print("تم.")
print("ملفات جديدة:",downloaded)
print("إجمالي ملفات القرآن:",len(files))
print("index:",ROOT+"/index.json")
print("================================")
