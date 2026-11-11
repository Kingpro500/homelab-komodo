import io, time, threading, torch
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, Response
from diffusers import Flux2KleinPipeline
M="/models/FLUX.2-klein-4B"
pipe=Flux2KleinPipeline.from_pretrained(M,torch_dtype=torch.bfloat16)
pipe.enable_sequential_cpu_offload()
lock=threading.Lock()
app=FastAPI()
PAGE="""<!doctype html><meta charset=utf-8><title>FLUX.2 klein</title>
<body style="font-family:sans-serif;max-width:820px;margin:2em auto;background:#111;color:#eee">
<h2>FLUX.2 klein 4B</h2>
<form id=f><textarea name=prompt rows=4 style="width:100%" placeholder="Beskriv bildet..."></textarea><br>
Bredde <input name=w value=1024 size=5> Høyde <input name=h value=1024 size=5> Steg <input name=steps value=4 size=3> Seed <input name=seed value=-1 size=8>
<button>Lag bilde</button> <span id=s></span></form><img id=i style="max-width:100%;margin-top:1em">
<script>f.onsubmit=async e=>{e.preventDefault();s.textContent='Genererer...';const r=await fetch('/gen',{method:'POST',body:new FormData(f)});
if(!r.ok){s.textContent='Feil: '+await r.text();return}i.src=URL.createObjectURL(await r.blob());s.textContent='Ferdig'}</script>"""
@app.get("/",response_class=HTMLResponse)
def index(): return PAGE
@app.post("/gen")
def gen(prompt:str=Form(...),w:int=Form(1024),h:int=Form(1024),steps:int=Form(4),seed:int=Form(-1)):
    w=max(256,min(1536,w//16*16)); h=max(256,min(1536,h//16*16))
    g=torch.Generator("cpu").manual_seed(seed if seed>=0 else int(time.time()))
    with lock:
        img=pipe(prompt=prompt,width=w,height=h,num_inference_steps=steps,guidance_scale=1.0,generator=g).images[0]
    b=io.BytesIO(); img.save(b,"PNG"); return Response(b.getvalue(),media_type="image/png")
