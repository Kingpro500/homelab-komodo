// dockctl — minimal container control API for Homepage on CT109.
// Serves:
//   GET  /                          -> control panel (HTML, asks for token)
//   GET  /api/containers            -> [ {name, state} ] for ALL containers
//   POST /api/containers/:name/:a   -> :a in start|stop|restart
// All /api/* require `Authorization: Bearer <CONTROL_TOKEN>`.
// Talks to Docker via /var/run/docker.sock (mounted read-write).
'use strict';
const http = require('http');
const crypto = require('crypto');
const { execFile } = require('child_process');

const SOCKET = '/var/run/docker.sock';
const DOCKER = typeof process.env.DOCKER_HOST === 'undefined' && require('fs').existsSync(SOCKET);
// Ignore DOCKER_HOST: this container talks directly to the socket we mount.

function docker(method, path, cb) {
  // Docker Engine API over the unix socket.
  const httpMod = DOCKER ? http : null;
  if (!httpMod) return cb(new Error('docker socket not available'));
  const req = httpMod.request({
    socketPath: SOCKET, method, path
  }, (res) => {
    let body = '';
    res.on('data', (c) => body += c);
    res.on('end', () => cb(null, res.statusCode, body));
  });
  req.on('error', (e) => cb(e));
  req.end();
}

function dockerAction(name, action, cb) {
  const id = encodeURIComponent(name);
  const path = {
    start: `/v1.41/containers/${id}/start`,
    stop:  `/v1.41/containers/${id}/stop`,
    restart: `/v1.41/containers/${id}/restart`
  }[action];
  docker('POST', path, cb);
}

function safeEqual(a, b) {
  const ha = crypto.createHash('sha256').update(String(a)).digest();
  const hb = crypto.createHash('sha256').update(String(b)).digest();
  return crypto.timingSafeEqual(ha, hb);
}

function isAuthed(req) {
  const token = process.env.CONTROL_TOKEN || '';
  if (!token) return false;
  const auth = req.headers.authorization || '';
  const m = /^Bearer\s+(.+)$/i.exec(auth);
  return !!m && safeEqual(m[1], token);
}

function json(res, code, obj) {
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  });
  res.end(JSON.stringify(obj));
}

const PANEL = `<!doctype html><html lang="nb"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Docker-kontroll · CT109</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--tx:#e2e8f0;--mut:#94a3b8;--ok:#22c55e;--stop:#ef4444;--ac:#38bdf8}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--tx);padding:24px}
h1{font-size:1.2rem;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.wrap{max-width:860px;margin:0 auto}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
input{padding:8px 10px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:var(--tx)}
button{border:0;color:#fff;font-weight:600;cursor:pointer}
button:disabled{opacity:.4;cursor:not-allowed}
#save{background:#2563eb;padding:8px 14px;border-radius:8px}
table{width:100%;border-collapse:collapse;margin-top:16px;background:var(--card);border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #334155}
td.name{font-weight:600}.state{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.75rem}
.s-running{background:rgba(34,197,94,.15);color:var(--ok)}
.s-exited,.s-dead,.s-paused{background:rgba(239,68,68,.15);color:var(--stop)}
.btn{padding:5px 12px;border-radius:6px;font-size:.78rem}
.b-start{background:var(--ok)}.b-stop{background:var(--stop)}.b-restart{background:var(--ac)}
.badge{color:var(--mut);font-size:.75rem}
.err{color:var(--stop);min-height:18px}
</style></head><body><div class="wrap">
<h1>Docker-kontroll · CT109 <span class="badge" id="meta"></span></h1>
<div class="row">
 <input type="password" id="tok" placeholder="Bearer-token" style="flex:1" autocomplete="off">
 <button id="save">Lagre token</button>
 <button id="refresh" style="background:#64748b;padding:8px 14px;border-radius:8px">↻</button>
</div>
<div class="err" id="err"></div>
<table><thead><tr><th>Container</th><th>Status</th><th style="text-align:right">Handlinger</th></tr></thead>
<tbody id="rows"></tbody></table>
<p class="badge">Status oppdateres automatisk hvert 5. sekund. Stopp/start/restart kjører mot docker.sock på CT109.</p>
</div>
<script>
const tokEl=document.getElementById('tok'),rows=document.getElementById('rows'),
errEl=document.getElementById('err'),meta=document.getElementById('meta');
let token=localStorage.getItem('ct109_tok')||''; if(token)tokEl.value=token;
function setErr(m){errEl.textContent=m||''}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function api(path,method){
  const r=await fetch(path,{method:method||'GET',headers:{'Authorization':'Bearer '+token}});
  if(r.status===401)throw new Error('401 – sjekk token');
  if(!r.ok)throw new Error(r.status+' '+ (await r.text()));
  return r.json();
}
function render(list){
  rows.innerHTML=list.map(c=>{
    const up=c.state==='running';
    return '<tr><td class="name">'+esc(c.name)+'</td>'+
      '<td><span class="state '+(up?'s-running':'s-exited')+'">'+esc(c.state)+'</span></td>'+
      '<td style="text-align:right" class="row">'+
        (up?'<button class="btn b-stop" data-n="'+esc(c.name)+'" data-a="stop">Stopp</button>':'<button class="btn b-start" data-n="'+esc(c.name)+'" data-a="start">Start</button>')+
        '<button class="btn b-restart" data-n="'+esc(c.name)+'" data-a="restart">Restart</button>'+
      '</td></tr>';
  }).join('');
}
async function load(){
  try{const d=await api('/api/containers');meta.textContent=d.length+' containere';render(d);setErr('');}
  catch(e){setErr('Kunne ikke hente status: '+e.message)}
}
document.getElementById('save').onclick=()=>{token=tokEl.value;localStorage.setItem('ct109_tok',token);load();setErr('Token lagret i denne nettleseren.');};
document.getElementById('refresh').onclick=load;
rows.addEventListener('click',async ev=>{
  const b=ev.target.closest('button.btn');if(!b)return;b.disabled=true;setErr('');
  try{
    const r=await fetch('/api/containers/'+encodeURIComponent(b.dataset.n)+'/'+b.dataset.a,
      {method:'POST',headers:{'Authorization':'Bearer '+token}});
    if(r.status===401)throw new Error('401 – sjekk token');
    if(!r.ok)throw new Error((await r.text())||r.status);
    await new Promise(r=>setTimeout(r,400)); load();
  }catch(e){setErr(b.dataset.a+' feilet: '+e.message)}
  load();
});
load();setInterval(load,5000);
</script></body></html>`;

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = url.pathname;

  if (req.method === 'OPTIONS') { res.writeHead(204, {'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Authorization, Content-Type','Access-Control-Allow-Methods':'GET, POST, OPTIONS'}); return res.end(); }

  if (req.method === 'GET' && (p === '/' || p === '/panel')) {
    res.writeHead(200, {'Content-Type':'text/html; charset=utf-8'});
    return res.end(PANEL);
  }

  if (p === '/api/containers' && req.method === 'GET') {
    if (!isAuthed(req)) return json(res, 401, {error:'unauthorized'});
    return docker('GET','/v1.41/containers/json?all=1',(e,code,body)=>{
      if (e) return json(res, 500, {error:String(e)});
      let arr=[]; try { arr=JSON.parse(body); } catch(_) { return json(res,500,{error:'docker parse'}); }
      const out=arr.map(c=>({ name:c.Names&&c.Names[0]?c.Names[0].replace(/^\//,''):String(c.Id||'').slice(0,12), state:c.State||'unknown' }))
        .sort((a,b)=>a.name.localeCompare(b.name));
      return json(res, 200, out);
    });
  }

  const mm = /^\/api\/containers\/([^/]+)\/(start|stop|restart)$/.exec(p);
  if (mm && req.method === 'POST') {
    if (!isAuthed(req)) return json(res, 401, {error:'unauthorized'});
    const name = decodeURIComponent(mm[1]);
    const action = mm[2];
    return dockerAction(name, action, (e,code,body)=>{
      if (e) return json(res, 500, {error:String(e)});
      // 204 = OK, 304 = already in that state, 404 = no such container
      if (code===404) return json(res, 404, {error:'ukjent container'});
      if (code===304) return json(res, 200, {ok:true, note:'allerede i denne tilstanden'});
      if (code>=200&&code<300) return json(res, 200, {ok:true});
      return json(res, code||500, {error:body||String(code), dockerCode:code});
    });
  }

  json(res, 404, {error:'not found'});
});

const PORT = process.env.CONTROL_PORT || 3015;
server.listen(PORT, '0.0.0.0', () => console.log('dockctl listening on :'+PORT));
