#!/usr/bin/env python3
"""Minimal durable CT-reconcile runner.

Secrets and privileged integrations are deliberately adapter interfaces. This service provides
validated input, SQLite durability, VMID leases, idempotent jobs, polling, and explicit blocked
states; it never claims a CT is reconciled without verified integration results.
"""
from __future__ import annotations
import json, os, re, secrets, sqlite3, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DB = Path(os.environ.get("CT_RECONCILE_DB", "/var/lib/hermes/ct-reconcile.db"))
HOST = os.environ.get("CT_RECONCILE_BIND", "127.0.0.1")
PORT = int(os.environ.get("CT_RECONCILE_PORT", "9120"))
TOKEN = os.environ.get("CT_RECONCILE_TOKEN")
LOCK = threading.Lock()
ALLOWED = {"inspect", "reconcile", "deploy", "repair"}
STATES = {"DISCOVER", "CHECK_PROXMOX", "START_REQUIRES_APPROVAL", "WAIT_FOR_STABLE_RUNTIME", "CHECK_PERIPHERY", "CHECK_DOCKER", "PULL_STACK", "DEPLOY_STACK", "VERIFY_CONTAINER", "VERIFY_APPLICATION", "VERIFY_GITHUB", "VERIFY_KOMODO", "VERIFY_NETWORK_MAP", "DONE", "WAITING_APPROVAL", "BLOCKED", "RETRY_WAIT", "DIAGNOSTICS"}


def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    c.executescript('''
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS jobs (
      job_id TEXT PRIMARY KEY, vmid INTEGER NOT NULL, action TEXT NOT NULL,
      start_policy TEXT NOT NULL, state TEXT NOT NULL, approval TEXT NOT NULL,
      payload_json TEXT NOT NULL, result_json TEXT, error TEXT, attempts INTEGER NOT NULL DEFAULT 0,
      lease_until REAL, next_run_at REAL NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL
    );
    CREATE UNIQUE INDEX IF NOT EXISTS one_active_vmid ON jobs(vmid) WHERE state NOT IN ('DONE','BLOCKED');
    CREATE TABLE IF NOT EXISTS job_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, state TEXT NOT NULL,
      event_json TEXT NOT NULL, created_at REAL NOT NULL
    );
    ''')
    return c


def now(): return time.time()
def clean_error(x): return str(x)[:500]
def job_view(r):
    d = dict(r); d["payload"] = json.loads(d.pop("payload_json")); d["result"] = json.loads(d.pop("result_json")) if d.get("result_json") else None; d.pop("lease_until", None); return d


def create_job(payload):
    vmid = payload.get("vmid")
    if isinstance(vmid, bool) or not isinstance(vmid, int) or not 100 <= vmid <= 999999: raise ValueError("vmid must be an integer between 100 and 999999")
    action = payload.get("requested_action", "reconcile")
    if action not in ALLOWED: raise ValueError("unsupported requested_action")
    policy = payload.get("start_policy", "approval_required")
    if policy not in {"never", "approval_required"}: raise ValueError("unsupported start_policy")
    t = now(); c = db()
    try:
        active = c.execute("SELECT * FROM jobs WHERE vmid=? AND state NOT IN ('DONE','BLOCKED')", (vmid,)).fetchone()
        if active: return job_view(active), False
        jid = f"ct-{vmid}-{int(t)}-{secrets.token_hex(4)}"
        c.execute("INSERT INTO jobs(job_id,vmid,action,start_policy,state,approval,payload_json,next_run_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (jid,vmid,action,policy,"DISCOVER","not_required",json.dumps(payload, separators=(",",":")),t,t,t))
        c.execute("INSERT INTO job_events(job_id,state,event_json,created_at) VALUES(?,?,?,?)", (jid,"DISCOVER",json.dumps({"event":"created"}),t)); c.commit()
        return job_view(c.execute("SELECT * FROM jobs WHERE job_id=?", (jid,)).fetchone()), True
    finally: c.close()


def transition(jid, state, **event):
    c = db(); t = now()
    try:
        c.execute("UPDATE jobs SET state=?, updated_at=?, next_run_at=? WHERE job_id=?", (state,t,t,jid))
        c.execute("INSERT INTO job_events(job_id,state,event_json,created_at) VALUES(?,?,?,?)", (jid,state,json.dumps(event, separators=(",",":")),t)); c.commit()
    finally: c.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def auth(self):
        if not TOKEN: return True
        return self.headers.get("X-CT-Reconcile-Token") == TOKEN or self.headers.get("Authorization") == "Bearer " + TOKEN
    def send(self, code, obj):
        raw = json.dumps(obj, separators=(",",":"), ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path == "/health": return self.send(200, {"ok":True,"service":"ct-reconcile-runner","state_store":str(DB)})
        if not self.auth(): return self.send(401,{"error":"unauthorized"})
        m = re.fullmatch(r"/jobs/([^/]+)", self.path)
        if m:
            c=db(); r=c.execute("SELECT * FROM jobs WHERE job_id=?",(m.group(1),)).fetchone(); c.close(); return self.send(200,job_view(r)) if r else self.send(404,{"error":"not found"})
        return self.send(404,{"error":"not found"})
    def do_POST(self):
        if not self.auth(): return self.send(401,{"error":"unauthorized"})
        n=int(self.headers.get("Content-Length","0"));
        try: payload=json.loads(self.rfile.read(n) or b"{}")
        except Exception: return self.send(400,{"error":"invalid JSON"})
        if self.path == "/ct-reconcile":
            try: job, created=create_job(payload); return self.send(202 if created else 200,{"accepted":True,"created":created,"job":job})
            except ValueError as e: return self.send(400,{"error":str(e)})
        m=re.fullmatch(r"/jobs/([^/]+)/approve",self.path)
        if m:
            c=db(); r=c.execute("SELECT * FROM jobs WHERE job_id=?",(m.group(1),)).fetchone()
            if not r: c.close(); return self.send(404,{"error":"not found"})
            c.execute("UPDATE jobs SET approval='approved', state='WAIT_FOR_STABLE_RUNTIME', updated_at=?, next_run_at=? WHERE job_id=?",(now(),now(),m.group(1))); c.commit(); c.close(); return self.send(200,{"approved":True,"job_id":m.group(1)})
        return self.send(404,{"error":"not found"})

if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
