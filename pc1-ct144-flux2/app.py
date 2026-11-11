import io, time, gc, threading, torch
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, Response
from diffusers import Flux2KleinPipeline, Flux2Transformer2DModel, BitsAndBytesConfig as DBnb
from transformers import BitsAndBytesConfig as TBnb, Qwen3ForCausalLM
M="/models/FLUX.2-klein-4B"
lock=threading.Lock(); state={"mode":None,"pipe":None}
def load(mode):
    if state["mode"]==mode: return state["pipe"]
    state["pipe"]=None; state["mode"]=None; gc.collect(); torch.cuda.empty_cache()
    if mode=="fast":
        q=DBnb(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16)
        tr=Flux2Transformer2DModel.from_pretrained(M,subfolder="transformer",quantization_config=q,torch_dtype=torch.bfloat16)
        tq=TBnb(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16)
        te=Qwen3ForCausalLM.from_pretrained(M,subfolder="text_encoder",quantization_config=tq,torch_dtype=torch.bfloat16)
        p=Flux2KleinPipeline.from_pretrained(M,transformer=tr,text_encoder=te,torch_dtype=torch.bfloat16)
        p.vae.to("cuda")
    else:
        p=Flux2KleinPipeline.from_pretrained(M,torch_dtype=torch.bfloat16)
        p.enable_sequential_cpu_offload()
    state["pipe"]=p; state["mode"]=mode; return p
app=FastAPI()
PAGE="""<!doctype html><meta charset=utf-8><title>FLUX.2 klein</title>
<body style="font-family:sans-serif;max-width:820px;margin:2em auto;background:#111;color:#eee">
<h2>FLUX.2 klein 4B</h2>
<form id=f><textarea name=prompt rows=4 style="width:100%" placeholder="Beskriv bildet..."></textarea><br>
Bredde <input name=w value=768 size=5> Høyde <input name=h value=768 size=5> Steg <input name=steps value=4 size=3> Seed <input name=seed value=42 size=8>
<br><button name=mode value=fast>Kjapp (utkast)</button> <button name=mode value=hq>Oppgrader (full modell, 1024)</button> <span id=s></span></form>
<p style="color:#999;font-size:.9em">Oppgrader bruker samme prompt og seed, så du får «samme» bilde i høyere kvalitet. Bytte mellom modusene tar ca. 30–60 s ekstra.</p>
<img id=i style="max-width:100%;margin-top:1em">
<script>let b;f.querySelectorAll('button').forEach(x=>x.onclick=()=>b=x.value);
f.onsubmit=async e=>{e.preventDefault();const d=new FormData(f);d.set('mode',b);if(b=='hq'){d.set('w',1024);d.set('h',1024)}
s.textContent='Genererer...';const t=Date.now();const r=await fetch('/gen',{method:'POST',body:d});
if(!r.ok){s.textContent='Feil: '+await r.text();return}i.src=URL.createObjectURL(await r.blob());s.textContent='Ferdig ('+Math.round((Date.now()-t)/1000)+' s)'}</script>"""
@app.get("/",response_class=HTMLResponse)
def index(): return PAGE
@app.post("/gen")
def gen(prompt:str=Form(...),w:int=Form(768),h:int=Form(768),steps:int=Form(4),seed:int=Form(42),mode:str=Form("fast")):
    w=max(256,min(1536,w//16*16)); h=max(256,min(1536,h//16*16))
    g=torch.Generator("cpu").manual_seed(seed if seed>=0 else int(time.time()))
    with lock:
        p=load("fast" if mode=="fast" else "hq")
        img=p(prompt=prompt,width=w,height=h,num_inference_steps=steps,guidance_scale=1.0,generator=g).images[0]
    b=io.BytesIO(); img.save(b,"PNG"); return Response(b.getvalue(),media_type="image/png")
