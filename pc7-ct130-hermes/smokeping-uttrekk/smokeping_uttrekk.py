#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, math, subprocess, sys
from zoneinfo import ZoneInfo

POINTS = ['pc6','pc7','pc8','pc9']
TARGETS = [('Internet','ISPGateway','ISP-gateway'),('Internet','Cloudflare','Cloudflare'),('Internet','Quad9','Quad9'),('Internet','Google','Google'),('Infrastructure','OPNsense','OPNsense'),('NetworkGear','ACPro','Aksesspunkt'),('NetworkGear','EdgeSwitch','EdgeSwitch'),('Gaming','PS5','PS5')]
OUT='/srv/nettkart/www/smokeping.json'

def fetch(path, start, end):
    cmd=['ssh','pc6','pct','exec','113','--','docker','exec','smokeping','rrdtool','fetch',path,'AVERAGE','-r','3600','-s',str(int(start.timestamp())),'-e',str(int(end.timestamp()))]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    if p.returncode: raise RuntimeError(p.stderr.strip() or 'rrdtool fetch feilet')
    rows=[]
    for line in p.stdout.splitlines():
        if ':' not in line or line.lstrip().startswith('uptime'): continue
        stamp, rest=line.split(':',1)
        try: vals=[float(x) for x in rest.split()]
        except ValueError: continue
        if len(vals)>=3 and math.isfinite(vals[2]): rows.append((dt.datetime.fromtimestamp(int(stamp),dt.timezone.utc),vals[1],vals[2]))
    return rows

def stats(rows):
    if not rows: return {'median_ms':None,'verste_time_ms':None,'tap_prosent':None,'timer':0}
    med=[r[2] for r in rows]; loss=[r[1] for r in rows if math.isfinite(r[1])]
    return {'median_ms':round(sorted(med)[len(med)//2]*1000 if len(med)%2 else (sorted(med)[len(med)//2-1]+sorted(med)[len(med)//2])/2*1000,1),'verste_time_ms':round(max(med)*1000,1),'tap_prosent':round(sum(loss)/len(loss)/20*100,2) if loss else 0.0,'timer':len(rows)}

def selftest():
    assert stats([(dt.datetime.now(dt.timezone.utc),0,0.001),(dt.datetime.now(dt.timezone.utc),2,0.003)]) == {'median_ms':2.0,'verste_time_ms':3.0,'tap_prosent':5.0,'timer':2}
    assert stats([])['median_ms'] is None
    assert stats([(dt.datetime.now(dt.timezone.utc),float('nan'),float('nan') )])['timer']==0
    print('selvtest ok')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--selvtest',action='store_true'); ap.add_argument('--ikke-skriv',action='store_true'); a=ap.parse_args()
    if a.selvtest: selftest(); return
    tz=ZoneInfo('Europe/Oslo'); today=dt.datetime.now(tz).date(); dates=[today-dt.timedelta(days=i) for i in range(29,-1,-1)]
    start=dt.datetime.combine(dates[0],dt.time(),tzinfo=tz); end=dt.datetime.combine(today+dt.timedelta(days=1),dt.time(),tzinfo=tz)
    allrows={}
    for group,target,_ in TARGETS:
      for point in POINTS:
        suffix='' if point=='pc6' else '~'+point
        path=f'/data/{group}/{target}.rrd{suffix}'
        try: allrows[(group,target,point)]=fetch(path,start,end)
        except RuntimeError as e:
          if 'No such file' in str(e) or 'does not exist' in str(e): continue
          raise
    out={'generert':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'maal':[]}
    for group,target,name in TARGETS:
      obj={'navn':name,'gruppe':group,'dager':[]}
      for day in dates:
        p={}
        for point in POINTS:
          rows=[r for r in allrows.get((group,target,point),[]) if r[0].astimezone(tz).date()==day]
          p[point]=stats(rows)
        obj['dager'].append({'dato':day.isoformat(),'punkter':p})
      out['maal'].append(obj)
    text=json.dumps(out,ensure_ascii=False,separators=(',',':'))
    if a.ikke_skriv: print(text); return
    payload=text.encode(); import base64
    enc=base64.b64encode(payload).decode();    p=subprocess.run(['ssh','pc6','pct','exec','120','--','python3','-c',"import sys,base64,os; p='"+OUT+"'; t=p+'.tmp'; open(t,'wb').write(base64.b64decode(sys.stdin.buffer.read())); os.replace(t,p)"],input=enc,text=True,capture_output=True,timeout=60)
    if p.returncode: raise RuntimeError(p.stderr.strip())

if __name__=='__main__':
 try: main()
 except Exception as e: print(str(e),file=sys.stderr); sys.exit(1)
