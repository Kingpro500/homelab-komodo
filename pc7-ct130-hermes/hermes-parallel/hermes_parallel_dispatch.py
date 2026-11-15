#!/usr/bin/env python3
"""Conservative parallel A dispatcher; B/C are never executable."""
import argparse, concurrent.futures, json, os, threading, time
BASE=os.path.expanduser("~/.hermes/parallel"); STATE=os.path.join(BASE,"state.json"); LOCK=threading.Lock()
SEED=[{"id":"K44","class":"A","status":"B","ct":340,"reason":"avvek fra godkjent sikkerhetsomfang","auto":False},{"id":"K45","class":"B","status":"venter_pa_roger","ct":150,"reason":"manuell godkjenning kreves","auto":False},{"id":"K47","class":"A","status":"avsluttet","ct":0,"reason":"historisk oppgave avsluttet","auto":False}]
def load():
 os.makedirs(BASE,exist_ok=True)
 if not os.path.exists(STATE): json.dump({"consecutive_a_failures":0,"paused":False,"tasks":SEED},open(STATE,"w"),indent=2)
 return json.load(open(STATE))
def save(s):
 t=STATE+'.tmp'; json.dump(s,open(t,'w'),indent=2,sort_keys=True); os.replace(t,STATE)
def resources(t): return set(t.get('resources',[]))|{f"ct:{t['ct']}"}
def eligible(t): return t.get('class')=='A' and t.get('auto',True) and t.get('status')=='klar' and t.get('ct',0)>0
def plan(tasks):
 selected=[]; used=set()
 for t in tasks:
  if eligible(t) and not resources(t)&used:
   selected.append(t); used |= resources(t)
  if len(selected)==3: break
 return selected
def run_task(t):
 # Execution hook is intentionally absent: only an explicitly supplied safe adapter may execute.
 return {"id":t["id"],"status":"planned","reason":"no execution adapter configured"}
def self_test():
 ts=[{"id":"a1","class":"A","status":"klar","auto":True,"ct":101,"resources":["repository"]},{"id":"a2","class":"A","status":"klar","auto":True,"ct":102,"resources":["repository"]},{"id":"b","class":"B","status":"klar","auto":True,"ct":103,"resources":[]},{"id":"c","class":"C","status":"klar","auto":True,"ct":104,"resources":[]},{"id":"same","class":"A","status":"klar","auto":True,"ct":101,"resources":[]}]
 p=plan(ts)
 assert {x['id'] for x in p}=={'a1'} or len(p)==1, 'shared repository lock failed'
 ts[0]['resources']=[]; ts[1]['resources']=[]; p=plan(ts); assert {x['id'] for x in p}=={'a1','a2'},'two CTs not parallel'
 assert not any(x['class'] in ('B','C') for x in p),'B or C selected'
 assert len({x['ct'] for x in p})==len(p),'CT lock failed'
 return 'SELF-TEST OK: two independent A tasks, B nonblocking, C never runs, CT and resource locks work'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--self-test','--self-test-execution',dest='self_test',action='store_true'); ap.add_argument('--list-b',action='store_true'); ap.add_argument('--plan',action='store_true'); a=ap.parse_args()
 if a.self_test: print(self_test()); return 0
 s=load()
 if a.list_b:
  for t in s['tasks']:
   if t.get('status') in ('B','venter_pa_roger') or t.get('class')=='B': print(f"{t['id']}: {t.get('reason','')}")
  return 0
 if a.plan:
  if s.get('paused'): print('PAUSED'); return 2
  p=plan(s['tasks']); print(json.dumps([x['id'] for x in p])); return 0
 return 0
if __name__=='__main__': main()
