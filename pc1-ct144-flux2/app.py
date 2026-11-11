import io, os, json, time, gc, queue, threading, torch
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from diffusers import Flux2KleinPipeline, Flux2Transformer2DModel, BitsAndBytesConfig as DBnb
from transformers import BitsAndBytesConfig as TBnb, Qwen3ForCausalLM
M="/models/FLUX.2-klein-4B"; OUT="/models/output"; TH=OUT+"/thumbs"
os.makedirs(TH,exist_ok=True)
state={"mode":None,"pipe":None}
_ll=threading.Lock()
def load(mode):
    with _ll: return _load(mode)
def _load(mode):
    if state["mode"]==mode: return state["pipe"]
    state["pipe"]=None; state["mode"]=None; gc.collect(); torch.cuda.empty_cache()
    if mode=="fast":
        q=DBnb(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16)
        tr=Flux2Transformer2DModel.from_pretrained(M,subfolder="transformer",quantization_config=q,torch_dtype=torch.bfloat16)
        tq=TBnb(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16)
        te=Qwen3ForCausalLM.from_pretrained(M,subfolder="text_encoder",quantization_config=tq,torch_dtype=torch.bfloat16)
        p=Flux2KleinPipeline.from_pretrained(M,transformer=tr,text_encoder=te,torch_dtype=torch.bfloat16)
        p.vae.to("cuda"); p.vae.enable_tiling()
    else:
        p=Flux2KleinPipeline.from_pretrained(M,torch_dtype=torch.bfloat16)
        p.enable_sequential_cpu_offload(); p.vae.enable_tiling()
    state["pipe"]=p; state["mode"]=mode; return p
Q=queue.Queue(); jobs={}; cur={"id":None}; seq=[0]; jl=threading.Lock()
def worker():
    while True:
        jid=Q.get(); j=jobs[jid]; j["status"]="running"; cur["id"]=jid; t=time.time()
        try:
            p=load(j["mode"])
            g=torch.Generator("cpu").manual_seed(j["seed"])
            img=p(prompt=j["prompt"],width=j["w"],height=j["h"],num_inference_steps=j["steps"],guidance_scale=1.0,generator=g).images[0]
            name=time.strftime("%Y%m%d-%H%M%S")+f"_{j['mode']}_{j['seed']}"
            img.save(f"{OUT}/{name}.png")
            th=img.copy(); th.thumbnail((384,384)); th.convert("RGB").save(f"{TH}/{name}.jpg",quality=85)
            meta={k:j[k] for k in("prompt","w","h","steps","seed","mode")}; meta.update(name=name,secs=round(time.time()-t),created=time.time())
            json.dump(meta,open(f"{OUT}/{name}.json","w"),ensure_ascii=False)
            j.update(status="done",name=name,secs=meta["secs"])
        except Exception as e:
            j.update(status="error",error=str(e)[:300]); gc.collect(); torch.cuda.empty_cache()
        cur["id"]=None
def warm():
    try: load("fast")
    except Exception as e: print("warm-up feilet:",e,flush=True)
threading.Thread(target=warm,daemon=True).start()
threading.Thread(target=worker,daemon=True).start()
app=FastAPI()
def snap(): return sorted(({"id":i,**{k:v for k,v in j.items() if k!="prompt"},"prompt":j["prompt"][:80]} for i,j in jobs.items() if j["status"] in("queued","running","error")),key=lambda x:x["id"])
@app.post("/submit")
def submit(prompt:str=Form(...),w:int=Form(1920),h:int=Form(1080),steps:int=Form(4),seed:int=Form(42),mode:str=Form("fast")):
    w=max(256,min(2048,w//16*16)); h=max(256,min(2048,h//16*16))
    if seed<0: seed=int(time.time())%2**31
    with jl:
        seq[0]+=1; jid=seq[0]
        jobs[jid]=dict(status="queued",prompt=prompt,w=w,h=h,steps=steps,seed=seed,mode="fast" if mode=="fast" else "hq",t0=time.time())
    Q.put(jid); return {"id":jid}
@app.get("/status")
def status():
    for i in [i for i,j in jobs.items() if j["status"]=="done" and time.time()-j["t0"]>3600]: jobs.pop(i)
    return {"jobs":snap(),"loaded":state["mode"],"running":cur["id"]}
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
PAGE=open(os.path.dirname(os.path.abspath(__file__))+"/page.html").read()
@app.get("/",response_class=HTMLResponse)
def index(): return PAGE
