import json, os, re, time, urllib.request, urllib.parse, csv
UA={"User-Agent":"OscarPosterFetcher/1.0 (sumerim@gmail.com)"}
def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60) as r: return r.read()
        except Exception as e:
            time.sleep(2+i*3); err=e
    raise err
q="""SELECT ?film ?filmLabel ?t ?article WHERE {
 ?film wdt:P31/wdt:P279* wd:Q11424. ?film p:P166 ?s. ?s ps:P166 wd:Q102427. OPTIONAL{?s pq:P585 ?t}
 ?article schema:about ?film; schema:isPartOf <https://en.wikipedia.org/>.
 SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } }"""
d=json.loads(get("https://query.wikidata.org/sparql?format=json&query="+urllib.parse.quote(q)))
rows={}
for b in d["results"]["bindings"]:
    t=b.get("t",{}).get("value","")[:4]
    title=urllib.parse.unquote(b["article"]["value"].rsplit("/",1)[1])
    rows.setdefault(title,(t,b["filmLabel"]["value"]))
out=os.path.expanduser("~/Desktop/oscar_en_iyi_film_afisleri"); os.makedirs(out,exist_ok=True)
meta=[]
for title,(yr,label) in sorted(rows.items(),key=lambda x:x[1][0]):
    p=json.loads(get("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageprops&ppprop=page_image&redirects=1&titles="+urllib.parse.quote(title)))
    pg=next(iter(p["query"]["pages"].values()))
    img=pg.get("pageprops",{}).get("page_image"); src=None
    if not img:
        w=json.loads(get("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvslots=main&redirects=1&titles="+urllib.parse.quote(title)))
        txt=next(iter(w["query"]["pages"].values()))["revisions"][0]["slots"]["main"]["*"]
        m=re.search(r"\|\s*image\s*=\s*(?:\[\[)?(?:File:|Image:)?([^\n|\]]+)",txt)
        if m and m.group(1).strip(): img=m.group(1).strip().replace(" ","_")
    if img:
        ii=json.loads(get("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url&titles="+urllib.parse.quote("File:"+img)))
        src=next(iter(ii["query"]["pages"].values()))["imageinfo"][0]["url"]
    fn=""
    if src:
        ext=os.path.splitext(urllib.parse.urlparse(src).path)[1].lower() or ".jpg"
        safe=re.sub(r"[^\w\- ]","",label).strip().replace(" ","_")
        fn=f"{yr}_{safe}{ext}"
        if not os.path.exists(os.path.join(out,fn)):
            open(os.path.join(out,fn),"wb").write(get(src)); time.sleep(0.5)
    meta.append({"yil":yr,"film":label,"wikipedia":"https://en.wikipedia.org/wiki/"+urllib.parse.quote(title),"afis_dosya":fn,"afis_url":src or ""})
    print(yr,label,"OK" if fn else "AFİŞ YOK")
with open(os.path.join(out,"liste.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(meta[0].keys())); w.writeheader(); w.writerows(meta)
print(len(meta),"film")
