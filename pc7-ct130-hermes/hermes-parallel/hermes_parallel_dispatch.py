#!/usr/bin/env python3
"""Conservative autonomous A dispatcher with one-shot rollback semantics."""
import argparse, concurrent.futures, json, os, subprocess, threading, time
BASE=os.path.expanduser("~/.hermes/parallel"); STATE=os.path.join(BASE,"state.json"); LOCK=threading.Lock()
SEED=[{"id":"K44","class":"A","status":"B","ct":340,"reason":"avvek fra godkjent sikkerhetsomfang","auto":False},{"id":"K45","class":"B","status":"venter_pa_roger","ct":150,"reason":"manuell godkjenning kreves","auto":False},{"id":"K47","class":"A","status":"avsluttet","ct":0,"reason":"historisk oppgave avsluttet","auto":False}]
def load():
 os.makedirs(BASE,exist_ok=True)
 if not os.path.exists(STATE): json.dump({"consecutive_a_failures":0,"paused":False,"tasks":SEED},open(STATE,"w"),indent=2)
 return json.load(open(STATE))
def save(s):
 t=STATE+'.tmp'; json.dump(s,open(t,'w'),indent=2,sort_keys=True); os.replace(t,STATE)
def resources(t): return set(t.get('resources',[]))|{f"ct:{t['ct']}"}
def eligible(t): return t.get('class')=='A' and t.get('auto',True) and t.get('status')=='klar' and t.get('ct',0)>0 and t.get('node') and t.get('change') and t.get('healthcheck') and t.get('rollback')
def plan(tasks):
 selected=[]; used=set()
 for t in tasks:
  if eligible(t) and not resources(t)&used:
   selected.append(t); used |= resources(t)
  if len(selected)==3: break
 return selected
def remote(node, command, timeout=90):
 p=subprocess.run(['ssh','-o','BatchMode=yes',node,command],capture_output=True,text=True,timeout=timeout)
 if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip() or f'command failed: {p.returncode}')
 return p.stdout.strip()
def run_task(t):
 stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime()); snap=f"hermes-a-{t['id'].lower()}-{stamp}"
 result={"id":t["id"],"ct":t["ct"],"snapshot":snap,"status":"failed"}
 try:
  desc=f"Hermes A {t['id']}; behold snapshot for rollback"
  remote(t['node'],f"pct snapshot {int(t['ct'])} {snap} --description {json.dumps(desc)}")
  remote(t['node'],f"pct exec {int(t['ct'])} -- sh -c {json.dumps(t['change'])}")
  remote(t['node'],f"pct exec {int(t['ct'])} -- sh -c {json.dumps(t['healthcheck'])}")
  result['status']='done'; return result
 except Exception as exc:
  result['error']=str(exc)
  try: remote(t['node'],f"pct exec {int(t['ct'])} -- sh -c {json.dumps(t['rollback'])}")
  except Exception as rollback_exc: result['rollback_error']=str(rollback_exc)
  return result
def self_test():
 ts=[{"id":"a1","class":"A","status":"klar","auto":True,"ct":101,"resources":["repository"]},{"id":"a2","class":"A","status":"klar","auto":True,"ct":102,"resources":["repository"]},{"id":"b","class":"B","status":"klar","auto":True,"ct":103},{"id":"c","class":"C","status":"klar","auto":True,"ct":104},{"id":"same","class":"A","status":"klar","auto":True,"ct":101}]
 assert len(plan(ts))==0, 'undeclared adapters must not run'
 ts[0].update(node='pc7',change='true',healthcheck='true',rollback='true'); ts[1].update(node='pc8',change='true',healthcheck='true',rollback='true'); ts[0]['resources']=[]; ts[1]['resources']=[]
 assert {x['id'] for x in plan(ts)}=={'a1','a2'}; return 'EXECUTION-TEST OK: declared A adapters only; B/C blocked; CT/resource locks enforced'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--list-b',action='store_true'); ap.add_argument('--plan',action='store_true'); ap.add_argument('--execute',action='store_true'); a=ap.parse_args()
 if a.self_test: print(self_test()); return 0
 s=load()
 if a.list_b:
  for t in s['tasks']:
   if t.get('status') in ('B','venter_pa_roger') or t.get('class')=='B': print(f"{t['id']}: {t.get('reason','')}")
  return 0
 if s.get('paused'): print('PAUSED'); return 2
 p=plan(s['tasks'])
 if a.plan: print(json.dumps([x['id'] for x in p])); return 0
 if a.execute:
  results=[]
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: results=list(ex.map(run_task,p))
  failures=[r for r in results if r['status']!='done']; s['a_failures']=s.get('a_failures',[])+failures; s['consecutive_a_failures']=s.get('consecutive_a_failures',0)+(1 if failures else 0)
  if failures:
   s['paused']=s['consecutive_a_failures']>=3
   for t in s['tasks']:
    if any(r['id']==t['id'] for r in failures): t['status']='B'; t['reason']='A-feil; tilbakeføring utført eller krever kontroll'
  else:
   for t in s['tasks']:
    if any(r['id']==t['id'] for r in results): t['status']='utført'
   s['consecutive_a_failures']=0
  save(s); print(json.dumps(results,sort_keys=True)); return 1 if failures else 0
 print(json.dumps([x['id'] for x in p])); return 0
if __name__=='__main__': raise SystemExit(main())
