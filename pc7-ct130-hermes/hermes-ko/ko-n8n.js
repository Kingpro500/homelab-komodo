// hermes-ko: oppgavekø for Hermes. Tilstand ligger i workflowens static data.
// Kilde: GitHub homelab-komodo, pc7-ct130-hermes/hermes-ko/ko-n8n.js
const st = $getWorkflowStaticData('global');
st.tasks = st.tasks || []; st.seq = st.seq || 0;
const b = ($json && $json.body) || {};
const now = new Date().toISOString();
const find = id => st.tasks.find(t => t.id === id);
const APEN = ['ny', 'godkjent', 'kjorer'];
const kort = t => ({ id: t.id, tittel: t.tittel, status: t.status, fase: t.fase || null, godkjenning: t.godkjenning,
  opprettet: t.opprettet, endret: t.endret, sammendrag: t.sammendrag || null });
const S = (v, n) => String(v === undefined || v === null ? '' : v).slice(0, n);
let out;
switch (b.action) {
  case 'add': {
    if (!b.tittel || !b.oppgave || !b.kontroll) { out = { ok: false, error: 'krever tittel, oppgave og kontroll' }; break; }
    const t = { id: 'k' + (++st.seq), tittel: S(b.tittel, 120), oppgave: S(b.oppgave, 12000), kontroll: S(b.kontroll, 2000),
      godkjenning: b.godkjenning === 'claude' ? 'claude' : 'ai', status: 'ny', opprettet: now, endret: now, logg: [] };
    st.tasks.push(t); out = { ok: true, id: t.id }; break;
  }
  case 'next': {
    for (const t of st.tasks) {
      if (t.status === 'kjorer' && Date.now() - Date.parse(t.startet || t.endret) > 3 * 3600 * 1000) {
        t.status = 'feilet'; t.sammendrag = 'Kjøreren svarte ikke på tre timer.'; t.endret = now;
      }
    }
    if (st.tasks.some(t => t.status === 'kjorer')) { out = { ok: true, task: null, grunn: 'opptatt' }; break; }
    const t = st.tasks.find(x => x.status === 'godkjent') || st.tasks.find(x => x.status === 'ny');
    if (!t) { out = { ok: true, task: null }; break; }
    t.fase = t.status === 'godkjent' ? 'utfor' : 'forslag';
    t.status = 'kjorer'; t.startet = now; t.endret = now;
    out = { ok: true, task: t }; break;
  }
  case 'update': {
    const t = find(b.id); if (!t) { out = { ok: false, error: 'ukjent id' }; break; }
    if (b.status) t.status = S(b.status, 30);
    for (const k of ['forslag', 'vurdering', 'resultat', 'sluttvurdering', 'kontroll_ut', 'sammendrag']) {
      if (b[k] !== undefined) t[k] = S(b[k], 16000);
    }
    if (b.logg) t.logg.push(now + ' ' + S(b.logg, 400));
    t.endret = now;
    out = { ok: true, igjen: st.tasks.filter(x => APEN.includes(x.status)).length }; break;
  }
  case 'approve': {
    const t = find(b.id);
    if (!t || t.status !== 'venter_godkjenning') { out = { ok: false, error: 'oppgaven venter ikke på godkjenning' }; break; }
    t.status = 'godkjent'; t.godkjent_av = S(b.av || 'ukjent', 30); t.endret = now; out = { ok: true }; break;
  }
  case 'reject': {
    const t = find(b.id); if (!t) { out = { ok: false, error: 'ukjent id' }; break; }
    t.tilbakemelding = S(b.tilbakemelding, 4000); t.status = b.parker ? 'parkert' : 'ny'; t.endret = now; out = { ok: true }; break;
  }
  case 'retry': {
    const t = find(b.id); if (!t) { out = { ok: false, error: 'ukjent id' }; break; }
    t.status = 'ny'; t.endret = now; out = { ok: true }; break;
  }
  case 'get': { const t = find(b.id); out = t ? { ok: true, task: t } : { ok: false, error: 'ukjent id' }; break; }
  case 'list': { out = { ok: true, tasks: st.tasks.map(kort) }; break; }
  case 'purge': {
    const cut = Date.now() - 14 * 86400 * 1000;
    st.tasks = st.tasks.filter(t => APEN.includes(t.status) || t.status === 'venter_godkjenning' || Date.parse(t.endret) > cut);
    out = { ok: true, igjen: st.tasks.length }; break;
  }
  default: out = { ok: false, error: 'gyldig action: add, next, update, approve, reject, retry, get, list, purge' };
}
return [{ json: out }];
