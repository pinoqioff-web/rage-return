import os,json

root="assets/quran"
themes=json.load(open(root+"/themes.json",encoding="utf-8"))
files=[]

for theme in themes:
    d=os.path.join(root,theme)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.lower().endswith((".mp3",".m4a",".ogg",".wav")):
            files.append({
                "file":"/assets/quran/"+theme+"/"+f,
                "theme":theme
            })

# إزالة التكرار
seen=set()
out=[]
for x in files:
    if x["file"] not in seen:
        seen.add(x["file"])
        out.append(x)

with open(root+"/index.json","w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=2)

print("تم إنشاء index.json")
print("عدد الملفات:",len(out))
print("عدد التصنيفات:",len(themes))
