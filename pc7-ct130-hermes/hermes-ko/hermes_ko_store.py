#!/usr/bin/env python3
"""Durable, local queue API for Hermes.  No queue state lives in n8n."""
import datetime, json, os, secrets, sqlite3, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, ".hermes", "ko")
DB = os.path.join(DIR, "hermes-ko.sqlite3")
ENV = os.path.join(HOME, ".hermes", "ko.env")
LANES = {"infra", "general", "diagnostics", "file-read", "network-map-read", "inventory"}
OPEN = {"ny", "godkjent", "kjorer"}
# Antall samtidige workers per lane (standard 1). Ressurslåsene (f.eks. ct:130) hindrer at
# to oppgaver rører samme CT samtidig. Må stemme med SLOTS i hermes_ko.py og med antall
# hermes-ko-<lane>[-N].timer på CT130.
SLOTS = {"infra": 3}
COLS = ("id,title,task,check_cmd,approval,lane,resources,status,phase,worker_id,lock_id,"
        "summary,feedback,created_at,updated_at,started_at")

def lane_keys(lane):
    return ["lane:" + lane] + ["lane:%s#%d" % (lane, i) for i in range(2, SLOTS.get(lane, 1) + 1)]

def token():
    with open(ENV, encoding="utf-8") as f:
        for line in f:
            if line.startswith("KO_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("KO_TOKEN mangler")

def connect():
    os.makedirs(DIR, mode=0o700, exist_ok=True)
    db = sqlite3.connect(DB, timeout=15, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, task TEXT NOT NULL, check_cmd TEXT NOT NULL,
        approval TEXT NOT NULL, lane TEXT NOT NULL, resources TEXT NOT NULL, status TEXT NOT NULL,
        phase TEXT, worker_id TEXT, lock_id TEXT, summary TEXT, feedback TEXT,
        created_at REAL NOT NULL, updated_at REAL NOT NULL, started_at REAL
      );
      CREATE TABLE IF NOT EXISTS locks (key TEXT PRIMARY KEY, lock_id TEXT NOT NULL, task_id TEXT NOT NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE);
      CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, task_id TEXT, at REAL NOT NULL, message TEXT NOT NULL);
    """)
    # Forslag og kontrollørens vurdering må overleve mellom forslag og utføring (godkjenning: claude).
    have = {r[1] for r in db.execute("PRAGMA table_info(tasks)")}
    # Sluttresultatet (utførers rapport, kontrollutskrift og sluttkontrollørens begrunnelse) lagres også.
    for col in ("proposal", "review", "result", "check_output", "final_review"):
        if col not in have:
            try:
                db.execute("ALTER TABLE tasks ADD COLUMN %s TEXT" % col)
            except sqlite3.OperationalError as e:  # to samtidige tilkoblinger kan ha lagt den til
                if "duplicate column" not in str(e): raise
    os.chmod(DB, 0o600)
    return db

def row(t):
    if not t: return None
    d = dict(t); d["tittel"] = d.pop("title"); d["oppgave"] = d.pop("task"); d["kontroll"] = d.pop("check_cmd")
    d["godkjenning"] = d.pop("approval"); d["kategori"] = d.pop("lane"); d["ressurser"] = json.loads(d.pop("resources"))
    d["fase"] = d.pop("phase"); d["sammendrag"] = d.pop("summary"); d["tilbakemelding"] = d.pop("feedback")
    d["forslag"] = d.pop("proposal", None) or ""; d["vurdering"] = d.pop("review", None) or ""
    d["resultat"] = d.pop("result", None) or ""; d["kontroll_ut"] = d.pop("check_output", None) or ""
    d["sluttvurdering"] = d.pop("final_review", None) or ""
    for old, new in (("created_at","opprettet"),("updated_at","endret"),("started_at","startet")):
        d[new] = d.pop(old)
    return d

def event(db, task_id, text): db.execute("INSERT INTO events(task_id,at,message) VALUES(?,?,?)", (task_id,time.time(),text[:4000]))
def release(db, task_id): db.execute("DELETE FROM locks WHERE task_id=?", (task_id,))
def recover(db):
    cutoff=time.time()-3*3600
    stale=db.execute("SELECT id FROM tasks WHERE status='kjorer' AND started_at<?",(cutoff,)).fetchall()
    for x in stale:
        db.execute("UPDATE tasks SET status='feilet',summary=?,updated_at=? WHERE id=?",("stale worker: ingen heartbeat eller avslutning innen tre timer",time.time(),x["id"]))
        release(db,x["id"]); event(db,x["id"],"stale worker lock released")
    # En worker som er død (prosessen finnes ikke lenger på denne maskinen) slipper lanen med en gang.
    # worker_id er «<lane>-<maskin>-<pid>» (hermes_ko.py). Andre worker_id-er faller til tre-timersregelen.
    host = "-" + os.uname().nodename + "-"
    for x in db.execute("SELECT id,worker_id FROM tasks WHERE status='kjorer' AND started_at<?", (time.time()-60,)).fetchall():
        w = x["worker_id"] or ""; pid = w.rsplit("-", 1)[-1]
        if host in w and pid.isdigit() and not os.path.exists("/proc/" + pid):
            db.execute("UPDATE tasks SET status='feilet',summary=?,updated_at=? WHERE id=?",
                       ("worker døde (prosess %s finnes ikke); lanen er frigitt" % pid, time.time(), x["id"]))
            release(db, x["id"]); event(db, x["id"], "død worker %s: lås frigitt" % w)
    db.execute("DELETE FROM locks WHERE task_id NOT IN (SELECT id FROM tasks WHERE status='kjorer')")

def stamp(value):
    if isinstance(value, (int, float)): return float(value)
    if not value: return time.time()
    return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()

def migrate(payload):
    """Import n8n staticData once. Running work is made failed, never resumed."""
    state = payload.get("global", payload)
    tasks = state.get("tasks", [])
    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        if db.execute("SELECT count(*) FROM tasks").fetchone()[0]:
            raise RuntimeError("SQLite-køen er ikke tom; migrering avbrutt")
        for source in tasks:
            status = source.get("status", "ny")
            if status == "kjorer": status = "feilet"
            ident = str(source["id"])
            created, updated = stamp(source.get("opprettet")), stamp(source.get("endret"))
            summary = source.get("sammendrag")
            if source.get("status") == "kjorer":
                summary = "migrert som feilet: tidligere worker var ikke verifiserbart levende"
            db.execute("INSERT INTO tasks(" + COLS + ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                ident, source.get("tittel", "")[:120], source.get("oppgave", "")[:12000],
                source.get("kontroll", "")[:2000], source.get("godkjenning", "ai"),
                source.get("kategori", "general"), json.dumps(source.get("ressurser", [])), status,
                source.get("fase"), None, None, str(summary or "")[:500],
                str(source.get("tilbakemelding", ""))[:4000], created, updated, None))
            for item in source.get("logg", []): event(db, ident, str(item))
        db.execute("COMMIT")
        return len(tasks)
    except Exception:
        db.execute("ROLLBACK"); raise
    finally: db.close()

def handle(p):
    action=p.get("action"); now=time.time(); db=connect()
    try:
      db.execute("BEGIN IMMEDIATE"); recover(db)
      if action=="add":
        if not all(p.get(k) for k in ("tittel","oppgave","kontroll")): return {"ok":False,"error":"krever tittel, oppgave og kontroll"}
        lane=p.get("kategori","general");
        if lane not in LANES: return {"ok":False,"error":"ugyldig kategori"}
        seq=db.execute("SELECT COALESCE(MAX(CAST(SUBSTR(id,2) AS INT)),0)+1 FROM tasks").fetchone()[0]; ident="k%d"%seq
        resources=sorted(set(str(x)[:120] for x in p.get("ressurser",[]) if x))
        db.execute("INSERT INTO tasks(" + COLS + ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(ident,p["tittel"][:120],p["oppgave"][:12000],p["kontroll"][:2000],"claude" if p.get("godkjenning")=="claude" else "ai",lane,json.dumps(resources),"ny",None,None,None,None,None,now,now,None))
        event(db,ident,"created"); return {"ok":True,"id":ident}
      if action=="list": return {"ok":True,"tasks":[row(x) for x in db.execute("SELECT * FROM tasks ORDER BY CAST(SUBSTR(id,2) AS INT)")]}
      if action=="get": return {"ok":True,"task":row(db.execute("SELECT * FROM tasks WHERE id=?",(p.get("id"),)).fetchone())}
      if action=="next":
        lane=p.get("lane"); worker=p.get("worker_id","")
        if lane not in LANES or not worker: return {"ok":False,"error":"next krever lane og worker_id"}
        slot=next((k for k in lane_keys(lane) if not db.execute("SELECT 1 FROM locks WHERE key=?",(k,)).fetchone()),None)
        if slot is None: return {"ok":True,"task":None,"grunn":"lane-opptatt"}
        for t in db.execute("SELECT * FROM tasks WHERE lane=? AND status IN ('ny','godkjent') ORDER BY CAST(SUBSTR(id,2) AS INT)",(lane,)):
          resources=json.loads(t["resources"])
          if any(db.execute("SELECT 1 FROM locks WHERE key=?",("resource:"+r,)).fetchone() for r in resources): continue
          lock="l"+secrets.token_urlsafe(12); phase="utfor" if t["status"]=="godkjent" else "forslag"
          db.execute("UPDATE tasks SET status='kjorer',phase=?,worker_id=?,lock_id=?,started_at=?,updated_at=? WHERE id=?",(phase,worker,lock,now,now,t["id"]))
          db.execute("INSERT INTO locks VALUES(?,?,?)",(slot,lock,t["id"]))
          for r in resources: db.execute("INSERT INTO locks VALUES(?,?,?)",("resource:"+r,lock,t["id"]))
          return {"ok":True,"task":row(db.execute("SELECT * FROM tasks WHERE id=?",(t["id"],)).fetchone()),"worker_id":worker,"lock_id":lock}
        return {"ok":True,"task":None,"grunn":"ingen-ledig-oppgave"}
      if action=="update":
        t=db.execute("SELECT * FROM tasks WHERE id=?",(p.get("id"),)).fetchone()
        if not t or t["status"]!="kjorer" or p.get("worker_id")!=t["worker_id"] or p.get("lock_id")!=t["lock_id"]: return {"ok":False,"error":"lock_id eller worker_id avvist"}
        status=p.get("status",t["status"]); summary=p.get("sammendrag",t["summary"])
        db.execute("UPDATE tasks SET status=?,summary=?,updated_at=? WHERE id=?",(status,str(summary or "")[:500],now,t["id"]))
        if p.get("forslag"): db.execute("UPDATE tasks SET proposal=? WHERE id=?",(str(p["forslag"])[:20000],t["id"]))
        if p.get("vurdering"): db.execute("UPDATE tasks SET review=? WHERE id=?",(str(p["vurdering"])[:8000],t["id"]))
        for key, col, cap in (("resultat", "result", 20000), ("kontroll_ut", "check_output", 4000), ("sluttvurdering", "final_review", 8000)):
            if p.get(key): db.execute("UPDATE tasks SET %s=? WHERE id=?" % col, (str(p[key])[-cap:] if key == "kontroll_ut" else str(p[key])[:cap], t["id"]))
        if status in {"ferdig","ferdig_med_merknad","feilet","parkert","venter_godkjenning"}: release(db,t["id"])
        if p.get("logg"): event(db,t["id"],p["logg"])
        return {"ok":True,"igjen":db.execute("SELECT count(*) FROM tasks WHERE status IN ('ny','godkjent','kjorer')").fetchone()[0]}
      if action=="approve":
        db.execute("UPDATE tasks SET status='godkjent',updated_at=? WHERE id=? AND status='venter_godkjenning'",(now,p.get("id"))); return {"ok":db.total_changes>0}
      if action=="reject":
        status="parkert" if p.get("parker") else "ny"; db.execute("UPDATE tasks SET status=?,feedback=?,updated_at=? WHERE id=?",(status,str(p.get("tilbakemelding", ""))[:4000],now,p.get("id"))); release(db,p.get("id")); return {"ok":db.total_changes>0}
      return {"ok":False,"error":"ukjent action"}
    finally:
      db.execute("COMMIT"); db.close()

class API(BaseHTTPRequestHandler):
  def do_POST(self):
    if self.path!="/queue" or self.headers.get("X-Ko-Token")!=token(): self.send_error(403); return
    try:
      body=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0")))); out=handle(body); raw=json.dumps(out,ensure_ascii=False).encode()
      self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    except Exception as e: self.send_error(500, str(e)[:200])
  def log_message(self,*args): pass

if __name__=="__main__":
  if sys.argv[1:]==["--migrate-stdin"]:
    print("migrated=" + str(migrate(json.load(sys.stdin))))
  else:
    ThreadingHTTPServer(("10.0.0.135",9121),API).serve_forever()
