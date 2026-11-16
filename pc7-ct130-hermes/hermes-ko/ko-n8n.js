// hermes-ko: lane- og ressurslåst oppgavekø. Static data oppdateres i ett Code-node-kall.
const st = $getWorkflowStaticData('global');
st.tasks = st.tasks || []; st.seq = st.seq || 0; st.locks = st.locks || {}; st.lockHistory = st.lockHistory || [];
for (const t of st.tasks) {
  if (!t.kategori) { t.kategori = 'general'; t.logg = t.logg || []; t.logg.push(new Date().toISOString() + ' migrert kategori til general'); t.endret = new Date().toISOString(); }
  if (!Array.isArray(t.ressurser)) t.ressurser = [];
}
const b = ($json && $json.body) || {};
const now = new Date().toISOString();
const APEN = ['ny', 'godkjent', 'kjorer'];
const LANES = ['infra', 'general', 'diagnostics', 'file-read', 'network-map-read', 'inventory'];
const S = (v, n) => String(v === undefined || v === null ? '' : v).slice(0, n);
const find = id => st.tasks.find(t => t.id === id);
const laneOf = v => v === undefined || v === null || v === '' ? 'general' : String(v);
const normResource = v => {
  const x = S(v, 120).trim().toLowerCase().replace(/[^a-z0-9:_-]+/g, '-').replace(/^-+|-+$/g, '');
  return x;
};
const resourcesOf = v => [...new Set((Array.isArray(v) ? v : (v ? [v] : [])).map(normResource).filter(Boolean))].sort();
const kort = t => ({ id:t.id, tittel:t.tittel, status:t.status, fase:t.fase||null, godkjenning:t.godkjenning,
  kategori:t.kategori, ressurser:t.ressurser, worker_id:t.worker_id||null, lock_id:t.lock_id||null,
  opprettet:t.opprettet, endret:t.endret, sammendrag:t.sammendrag||null });
const activeLock = key => st.locks[key];
const release = t => { for (const r of (t.ressurser || [])) if (st.locks['resource:'+r] === t.lock_id) delete st.locks['resource:'+r]; if (st.locks['lane:'+t.kategori] === t.lock_id) delete st.locks['lane:'+t.kategori]; };
const validLock = t => !!t && t.status === 'kjorer' && b.lock_id && b.lock_id === t.lock_id && b.worker_id === t.worker_id;
const setFail = (t, reason) => { t.status='feilet'; t.sammendrag=S(reason,500); t.endret=now; t.logg=t.logg||[]; t.logg.push(now+' '+S(reason,500)); release(t); };
let out;
switch (b.action) {
  case 'add': {
    if (!b.tittel || !b.oppgave || !b.kontroll) { out={ok:false,error:'krever tittel, oppgave og kontroll'}; break; }
    const kategori = laneOf(b.kategori); if (!LANES.includes(kategori)) { out={ok:false,error:'ugyldig kategori: bruk infra eller general',lost:false}; break; }
    const migrated = b.kategori === undefined || b.kategori === null || b.kategori === '';
    const t={id:'k'+(++st.seq),tittel:S(b.tittel,120),oppgave:S(b.oppgave,12000),kontroll:S(b.kontroll,2000),godkjenning:b.godkjenning==='claude'?'claude':'ai',kategori,ressurser:resourcesOf(b.ressurser),status:'ny',opprettet:now,endret:now,logg:[]};
    if (migrated) t.logg.push(now+' migrert kategori til general'); st.tasks.push(t); out={ok:true,id:t.id,kategori,ressurser:t.ressurser,migrert:migrated}; break;
  }
  case 'next': {
    const lane=laneOf(b.lane), worker=S(b.worker_id,120); if(!LANES.includes(lane)||!worker){out={ok:false,error:'next krever gyldig lane og worker_id'};break;}
    for(const t of st.tasks) if(t.status==='kjorer' && Date.now()-Date.parse(t.startet||t.endret)>3*3600*1000){
      t.lock_history=t.lock_history||[]; t.lock_history.push({lock_id:t.lock_id,worker_id:t.worker_id,action:'stale',at:now}); setFail(t,'stale worker: ingen heartbeat eller avslutning innen tre timer');
    }
    if(activeLock('lane:'+lane)){out={ok:true,task:null,grunn:'lane-opptatt'};break;}
    const t=st.tasks.find(x=>APEN.includes(x.status)&&laneOf(x.kategori)===lane&&!x.ressurser.some(r=>activeLock('resource:'+r)));
    if(!t){out={ok:true,task:null,grunn:'ingen-ledig-oppgave'};break;}
    const lock='l'+Date.now().toString(36)+Math.random().toString(36).slice(2,8); t.fase=t.status==='godkjent'?'utfor':'forslag'; t.status='kjorer'; t.startet=now;t.endret=now;t.worker_id=worker;t.lock_id=lock;
    st.locks['lane:'+lane]=lock; for(const r of t.ressurser) st.locks['resource:'+r]=lock; out={ok:true,task:t,worker_id:worker,lock_id:lock}; break;
  }
  case 'update': {
    const t=find(b.id); if(!validLock(t)){out={ok:false,error:'lock_id eller worker_id avvist'};break;}
    if(b.status) t.status=S(b.status,30); for(const k of ['forslag','vurdering','resultat','sluttvurdering','kontroll_ut','sammendrag']) if(b[k]!==undefined)t[k]=S(b[k],16000);
    if(b.logg){t.logg=t.logg||[];t.logg.push(now+' '+S(b.logg,400));} t.endret=now;
    if(['ferdig','ferdig_med_merknad','feilet','parkert','venter_godkjenning'].includes(t.status)){t.lock_history=t.lock_history||[];t.lock_history.push({lock_id:t.lock_id,worker_id:t.worker_id,action:t.status,at:now});release(t);}
    out={ok:true,igjen:st.tasks.filter(x=>APEN.includes(x.status)).length};break;
  }
  case 'retry': { const t=find(b.id); if(!t||t.status!=='feilet'||b.lock_id!==t.lock_id||b.worker_id!==t.worker_id){out={ok:false,error:'retry krever gjeldende lock_id og worker_id på feilet oppgave'};break;} t.lock_history=t.lock_history||[];t.lock_history.push({lock_id:t.lock_id,worker_id:t.worker_id,action:'retry',at:now});release(t);t.status='ny';t.endret=now;t.sammendrag='eksplisitt retry godkjent';out={ok:true};break; }
  case 'approve': {const t=find(b.id);if(!t||t.status!=='venter_godkjenning'){out={ok:false,error:'oppgaven venter ikke på godkjenning'};break;}t.status='godkjent';t.godkjent_av=S(b.av||'ukjent',30);t.endret=now;out={ok:true};break;}
  case 'reject': {const t=find(b.id);if(!t){out={ok:false,error:'ukjent id'};break;}if(t.status==='kjorer'&&!validLock(t)){out={ok:false,error:'lock_id eller worker_id avvist'};break;}t.tilbakemelding=S(b.tilbakemelding,4000);t.status=b.parker?'parkert':'ny';t.endret=now;if(t.status==='ny'||t.status==='parkert')release(t);out={ok:true};break;}
  case 'get': {const t=find(b.id);out=t?{ok:true,task:kort(t)}:{ok:false,error:'ukjent id'};break;}
  case 'list': {out={ok:true,tasks:st.tasks.map(kort)};break;}
  case 'purge': {const cut=Date.now()-14*86400000;st.tasks=st.tasks.filter(t=>APEN.includes(t.status)||t.status==='venter_godkjenning'||Date.parse(t.endret)>cut);out={ok:true,igjen:st.tasks.length};break;}
  default: out={ok:false,error:'gyldig action: add, next, update, approve, reject, retry, get, list, purge'};
}
return [{json:out}];