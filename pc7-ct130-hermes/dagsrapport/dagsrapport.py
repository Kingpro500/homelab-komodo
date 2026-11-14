#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, datetime as dt, html, json, re, shlex, subprocess, sys, urllib.request

DATA_URL='http://10.0.0.124:3020/linjekvalitet.json'
OLLAMA_URL='http://10.0.0.133:11434/api/generate'
REMOTE='/opt/moved-services/nettkart-repo/docs/network-map/linjekvalitet.html'
MONTHS=['jan','feb','mar','apr','mai','jun','jul','aug','sep','okt','nov','des']

def fetch(url, timeout=10):
    with urllib.request.urlopen(url, timeout=timeout) as r: return json.load(r)
def val(x, unit=''):
    if x is None: return 'ikke målt'
    if unit=='pct': return f'{x:.2f}'.replace('.',',')+' %'
    if unit=='int': return str(int(x))
    return f'{x:.1f}'.replace('.',',')+unit
def day_data(data):
    end=dt.datetime.now(dt.timezone.utc).astimezone().date()-dt.timedelta(days=1)
    rows={r.get('dato'):r for r in data.get('dager',[])}
    if end.isoformat() not in rows: raise RuntimeError('Gårsdagens rad mangler')
    return end,rows[end.isoformat()]
def points(end,r):
    up=r.get('oppetid') or {}; low=up.get('tjenester_laveste') or {}; cf=(r.get('latens') or {}).get('cloudflare') or {}
    internet=up.get('internett'); down=None if internet is None else (100-internet)/100*86400
    p1=f'Oppetid: Internett {val(internet,"pct")} (nede {val(down," sekunder")}), DNS ekstern {val(up.get("dns_ekstern"),"pct")}, gateway {val(up.get("gateway"),"pct")}, tjenester {val(up.get("tjenester"),"pct")}, lavest {html.escape(str(low.get("navn_lesbar") or low.get("navn") or "ikke målt"))} {val(low.get("prosent"),"pct")}.'
    p2=f'Linjen: karakter {html.escape(str(r.get("karakter") or "ikke målt"))}, bufferbloat {val(r.get("bufferbloat_ms")," ms")}, nedlasting {val(r.get("ned_median")," Mbit/s")}, opplasting {val(r.get("opp_median")," Mbit/s")}, WAN-brudd {val(r.get("wan_brudd"),"int")} ({val(r.get("wan_nedetid_s")," sekunder")}).'
    p3=f'Ping mot Cloudflare: median {val(cf.get("ping_median_ms")," ms")}, p95 {val(cf.get("ping_p95_ms")," ms")}, høyeste {val(cf.get("ping_maks_ms")," ms")}, pakketap {val(cf.get("pakketap_prosent"),"pct")}.'
    issues=[]
    if internet is not None and internet<99.9: issues.append('Internett under 99,9 %')
    if low.get('prosent') is not None and low['prosent']<99: issues.append('Laveste tjeneste under 99 %')
    if cf.get('pakketap_prosent') is not None and cf['pakketap_prosent']>1: issues.append('Pakketap mot Cloudflare over 1 %')
    if (r.get('wan_brudd') or 0)>=1: issues.append('Minst ett WAN-brudd')
    order=['A+','A','B','C','D','F']; grade=r.get('karakter')
    if grade in order and order.index(grade)>order.index('A'): issues.append('Karakter dårligere enn A')
    p4='Avvik: '+('Ingen avvik' if not issues else '; '.join(issues))+'.'
    return [p1,p2,p3,p4]
def ai(text):
    prompt='Punktene 1–4:\n'+text+'\nSkriv nøyaktig tre korte setninger på norsk bokmål som bare bruker tallene i teksten. Ingen andre tall.'
    req=json.dumps({'model':'qwen3:8b','prompt':prompt,'stream':False,'options':{'temperature':0.2}}).encode()
    with urllib.request.urlopen(urllib.request.Request(OLLAMA_URL,req,{'Content-Type':'application/json'}),timeout=90) as x: raw=json.load(x).get('response','')
    raw=re.sub(r'<think>.*?</think>','',raw,flags=re.S).strip()
    nums=re.findall(r'\d+(?:,\d+)?',raw); allowed=set(re.findall(r'\d+(?:,\d+)?',text.replace('.',',')))
    if len(raw)>500 or len(re.findall(r'[.!?](?:\s|$)',raw))!=3 or any(n not in allowed for n in nums): return None
    return raw
def read_remote():
    x=subprocess.run(['ssh','pc6','pct','exec','120','--','cat',REMOTE],capture_output=True,text=True,timeout=30)
    if x.returncode: raise RuntimeError(x.stderr.strip())
    return x.stdout
def write_remote(s):
    b=base64.b64encode(s.encode()).decode(); cmd=f"import sys,base64;open({REMOTE!r},'wb').write(base64.b64decode(sys.stdin.buffer.read()))"
    x=subprocess.run(['ssh','pc6','pct','exec','120','--','python3','-c',shlex.quote(cmd)],input=b,text=True,capture_output=True,timeout=30)
    if x.returncode: raise RuntimeError(x.stderr.strip())
def block(day,ps,summary):
    title=f'{day.day}. {MONTHS[day.month-1]}'
    out=f'<div id="dagsrapport" data-dag="{day.isoformat()}">\n<h2>I går, {title}</h2>\n<ul>\n'+''.join(f'<li>{html.escape(p,quote=False)}</li>\n' for p in ps)+'</ul>'
    if summary: out+=f'<p class="sub">Oppsummert av lokal AI (qwen3:8b): {html.escape(summary,quote=False)}</p>'
    return out+'\n</div>'
def update(src,new,day):
    ms=list(re.finditer(r'<div\b[^>]*\bid=["\']dagsrapport["\'][^>]*>.*?</div>',src,re.I|re.S))
    if len(ms)>1: raise RuntimeError('flere dagsrapport-blokker')
    if ms: return src[:ms[0].start()]+new+src[ms[0].end():]
    op=list(re.finditer(r'<[^>]*\bid=["\']oppetid["\'][^>]*>',src,re.I))
    if len(op)!=1: raise RuntimeError('id=oppetid mangler eller er ikke entydig')
    return src[:op[0].start()]+new+'\n'+src[op[0].start():]
def selftest():
    r={'karakter':'B','bufferbloat_ms':1.2,'ned_median':500.4,'opp_median':600,'wan_brudd':1,'wan_nedetid_s':4,'oppetid':{'internett':99.8,'dns_ekstern':99.9,'gateway':100,'tjenester':98,'tjenester_laveste':{'navn_lesbar':'x','prosent':98}},'latens':{'cloudflare':{'ping_median_ms':1,'ping_p95_ms':2,'ping_maks_ms':3,'pakketap_prosent':2}}}
    ps=points(dt.date(2026,1,1),r); assert 'Internett under' in ps[3] and 'Karakter dårligere' in ps[3]
    allowed=set(re.findall(r'\d+(?:,\d+)?', '\n'.join(ps).replace('.',','))); assert '999' not in allowed
    print('selvtest ok')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--selvtest',action='store_true'); ap.add_argument('--ikke-publiser',action='store_true'); a=ap.parse_args()
    if a.selvtest: selftest(); return
    day,r=day_data(fetch(DATA_URL)); ps=points(day,r); summary=None
    if not a.ikke_publiser:
        try: summary=ai('\n'.join(ps))
        except Exception: pass
    new=block(day,ps,summary)
    if a.ikke_publiser: print(new); return
    old=read_remote(); old_base=re.sub(r'(<div\b[^>]*\bid=["\']dagsrapport["\'][^>]*>.*?</div>)','',old,flags=re.I|re.S)
    old_match=re.search(r'<div\b[^>]*\bid=["\']dagsrapport["\'][^>]*>.*?</div>',old,re.I|re.S)
    if old_match:
        old_ps=re.findall(r'<li>(.*?)</li>',old_match.group(0),re.S); old_day=re.search(r'data-dag="([^"]+)"',old_match.group(0))
        if old_day and old_day.group(1)==day.isoformat() and old_ps==[html.escape(p,quote=False) for p in ps]: new=old_match.group(0)
    updated=update(old,new,day)
    if updated==old: print('uendret, publiserer ikke'); return
    write_remote(updated)
    x=subprocess.run(['ssh','pc6','pct','exec','120','--','/usr/local/sbin/nettkart-publish',f'Dagsrapport {day.day}. {MONTHS[day.month-1]}','--av','hermes','--berort','CT120'],capture_output=True,text=True,timeout=300)
    if x.returncode: raise RuntimeError(x.stderr.strip() or 'publisering feilet')
    print(x.stdout)
if __name__=='__main__':
    try: main()
    except Exception as e: print(str(e),file=sys.stderr); sys.exit(1)
