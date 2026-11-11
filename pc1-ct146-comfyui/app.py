# Galleri/visning som i CT144 (FLUX), men bak på ComfyUI (127.0.0.1:8188).
# Kjapp = turbo-LoRA + få steg. Full = modellen uten LoRA + flere steg.
import os, json, time, threading, queue, io, urllib.request as u
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from PIL import Image
C="http://127.0.0.1:8188"; OUT="/models/gallery"; TH=OUT+"/thumbs"; os.makedirs(TH,exist_ok=True)
UNET=os.environ["UNET"]; TE=os.environ["TE"]; VAE=os.environ["VAE"]; TITLE=os.environ.get("TITLE","ComfyUI")
LORA="krea2_turbo_lora_rank_64_bf16.safetensors"
def graph(j):
    fast=j["mode"]=="fast"; m=["1",0]
    w={"1":{"class_type":"UNETLoader","inputs":{"unet_name":UNET,"weight_dtype":"default"}},
       "2":{"class_type":"CLIPLoader","inputs":{"clip_name":TE,"type":"krea2"}},
       "3":{"class_type":"VAELoader","inputs":{"vae_name":VAE}},
       "4":{"class_type":"CLIPTextEncode","inputs":{"text":j["prompt"],"clip":["2",0]}},
       "5":{"class_type":"CLIPTextEncode","inputs":{"text":"","clip":["2",0]}},
       "6":{"class_type":"EmptySD3LatentImage","inputs":{"width":j["w"],"height":j["h"],"batch_size":1}}}
    if fast:
        w["10"]={"class_type":"LoraLoaderModelOnly","inputs":{"model":m,"lora_name":LORA,"strength_model":1.0}}; m=["10",0]
    w["7"]={"class_type":"KSampler","inputs":{"model":m,"positive":["4",0],"negative":["5",0],"latent_image":["6",0],"seed":j["seed"],"steps":j["steps"],"cfg":1.0 if fast else 3.5,"sampler_name":"euler","scheduler":"simple","denoise":1}}
    w["8"]={"class_type":"VAEDecode","inputs":{"samples":["7",0],"vae":["3",0]}}
    w["9"]={"class_type":"PreviewImage","inputs":{"images":["8",0]}}
    return w
def post(p,d): return json.load(u.urlopen(u.Request(C+p,json.dumps(d).encode(),{"Content-Type":"application/json"})))
Q=queue.Queue(); jobs={}; cur={"id":None}; seq=[0]; jl=threading.Lock(); last={"mode":None}
def worker():
    while True:
        jid=Q.get(); j=jobs[jid]; j["status"]="running"; cur["id"]=jid; t=time.time()
        try:
            pid=post("/prompt",{"prompt":graph(j)})["prompt_id"]
            while True:
                h=json.load(u.urlopen(f"{C}/history/{pid}"))
                if pid in h:
                    if h[pid]["status"]["status_str"]!="success": raise Exception(str(h[pid]["status"])[:250])
                    im=h[pid]["outputs"]["9"]["images"][0]; break
                time.sleep(2)
            raw=u.urlopen(f"{C}/view?filename={im['filename']}&subfolder={im['subfolder']}&type={im['type']}").read()
            img=Image.open(io.BytesIO(raw)); name=time.strftime("%Y%m%d-%H%M%S")+f"_{j['mode']}_{j['seed']}"
            img.save(f"{OUT}/{name}.png"); th=img.copy(); th.thumbnail((384,384)); th.convert("RGB").save(f"{TH}/{name}.jpg",quality=85)
            meta={k:j[k] for k in("prompt","w","h","steps","seed","mode")}; meta.update(name=name,secs=round(time.time()-t),created=time.time())
            json.dump(meta,open(f"{OUT}/{name}.json","w"),ensure_ascii=False)
            j.update(status="done",name=name,secs=meta["secs"]); last["mode"]=j["mode"]
        except Exception as e: j.update(status="error",error=str(e)[:300])
        cur["id"]=None
threading.Thread(target=worker,daemon=True).start()
app=FastAPI()
@app.post("/submit")
def submit(prompt:str=Form(...),w:int=Form(1920),h:int=Form(1080),steps:int=Form(0),seed:int=Form(42),mode:str=Form("fast")):
    w=max(256,min(2048,w//16*16)); h=max(256,min(2048,h//16*16)); mode="fast" if mode=="fast" else "hq"
    if steps<=0: steps=6 if mode=="fast" else 20
    if seed<0: seed=int(time.time())%2**31
    with jl:
        seq[0]+=1; jid=seq[0]
        jobs[jid]=dict(status="queued",prompt=prompt,w=w,h=h,steps=steps,seed=seed,mode=mode,t0=time.time())
    Q.put(jid); return {"id":jid}
@app.get("/status")
def status():
    for i in [i for i,j in jobs.items() if j["status"]=="done" and time.time()-j["t0"]>3600]: jobs.pop(i)
    return {"jobs":sorted(({"id":i,**{k:v for k,v in j.items() if k!="prompt"},"prompt":j["prompt"][:80]} for i,j in jobs.items() if j["status"] in("queued","running","error")),key=lambda x:x["id"]),"loaded":last["mode"],"running":cur["id"]}
@app.get("/gallery")
def gallery():
    out=[]
    for f in sorted(os.listdir(OUT),reverse=True):
        if f.endswith(".json"):
            try: out.append(json.load(open(OUT+"/"+f)))
            except Exception: pass
    return out[:200]
@app.get("/img/{name}")
def img(name:str,thumb:int=0):
    if "/" in name or ".." in name: raise HTTPException(400)
    p=f"{TH}/{name}.jpg" if thumb else f"{OUT}/{name}.png"
    if not os.path.exists(p): raise HTTPException(404)
    return FileResponse(p)
@app.delete("/img/{name}")
def delimg(name:str):
    if "/" in name or ".." in name or not name: raise HTTPException(400)
    n=0
    for p in (f"{OUT}/{name}.png",f"{OUT}/{name}.json",f"{TH}/{name}.jpg"):
        if os.path.exists(p): os.remove(p); n+=1
    if not n: raise HTTPException(404)
    return {"deleted":name}
PAGE=open(os.path.dirname(os.path.abspath(__file__))+"/page.html").read().replace("__TITLE__",TITLE)
@app.get("/",response_class=HTMLResponse)
def index(): return PAGE
