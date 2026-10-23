#!/usr/bin/env python3
"""Read-only media probes; bounded guest-only recovery. Invoked by forced SSH."""
import concurrent.futures, fcntl, json, os, pathlib, shlex, subprocess, time
import urllib.request, urllib.parse
STATE=pathlib.Path('/var/lib/media-recovery')
REMOTE=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=pc9','-o','UserKnownHostsFile=/etc/pve/nodes/pc9/ssh_known_hosts','-o','GlobalKnownHostsFile=/dev/null','-o','HostKeyAlgorithms=rsa-sha2-512,rsa-sha2-256','root@10.0.0.103']
SERVICES={'emby':('pc6',200,'http://10.0.0.150:8096'),'tunarr-pc6':('pc6',250,'http://10.0.0.123:8005'),'tunarr-pc9':('pc9',106,'http://10.0.0.122:8005')}
def decide(s,healthy,dependency,now):
 s['failures']=0 if healthy else s.get('failures',0)+1
 if healthy:return 'healthy'
 if not dependency:return 'blocked'
 if s['failures']<3:return 'observe'
 attempts=[t for t in s.get('attempts',[]) if now-t<86400]
 if len(attempts)>=2:return 'max-attempts'
 if attempts and now-attempts[-1]<1800:return 'cooldown'
 return 'repair'
def command(node,args,timeout=20):
 cmd=args if node=='pc6' else REMOTE+[shlex.join(args)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise RuntimeError('command failed: '+r.stderr[-180:])
 return r.stdout.strip()
def fetch(url,limit=1048576):
 with urllib.request.urlopen(url,timeout=8) as r:
  if r.status not in (200,206):raise RuntimeError('HTTP status')
  return r.read(limit)
def hls(base):
 channels=json.loads(fetch(base+'/api/channels'))
 if not channels:raise RuntimeError('no channels configured')
 ch=channels[0]['id'];url=base+'/stream/channels/'+ch+'?streamMode=hls'
 deadline=time.monotonic()+45
 while time.monotonic()<deadline:
  text=fetch(url).decode()
  if not text.startswith('#EXTM3U'):raise RuntimeError('not HLS')
  uris=[x.strip() for x in text.splitlines() if x.strip() and not x.startswith('#')]
  if not uris:time.sleep(2);continue
  target=urllib.parse.urljoin(url,uris[0])
  if '.m3u8' in target:url=target;continue
  data=fetch(target,65536)
  if len(data)<1024 or not (data[0]==71 or b'ftyp' in data[:64] or b'moof' in data[:64] or b'styp' in data[:64]):raise RuntimeError('not a video segment')
  return {'channel':ch,'bytes':len(data)}
 raise RuntimeError('HLS segment timeout')
def probe(fn):
 try:return {'ok':True,'detail':fn()}
 except Exception as e:return {'ok':False,'detail':str(e)[:220]}
# Bounded traversal only under this existing media folder. No writes, full-tree scans or symlink traversal.
READ_CODE="""import os,json,sys
root=sys.argv[1]
if len(sys.argv)>2:
 p=os.path.join(root,sys.argv[2])
 with open(p,'rb') as f: assert len(f.read(4096))>0
 print('read4096');sys.exit()
stack=[(root,0)];count=0
while stack and count<1000:
 d,depth=stack.pop()
 with os.scandir(d) as entries:
  for e in entries:
   count+=1
   if count>1000:break
   if e.is_file(follow_symlinks=False) and e.name.lower().endswith(('.mkv','.mp4','.avi','.ts')):
    with open(e.path,'rb') as f: assert len(f.read(4096))>0
    print(os.path.relpath(e.path,root));sys.exit()
   if depth<5 and e.is_dir(follow_symlinks=False):stack.append((e.path,depth+1))
raise RuntimeError('no bounded sample found')
"""
def host_read(node):
 mounts=json.loads(command(node,['findmnt','-J','-t','nfs,nfs4','-T','/mnt/pve/Tower-media']))
 mount=mounts['filesystems'][0]
 if mount['source']!='10.0.0.101:/mnt/user/media':raise RuntimeError('unexpected NFS source')
 return command(node,['timeout','12','python3','-c',READ_CODE,'/mnt/pve/Tower-media/3 Folder Emby/James Bond'])
def guest_probe(name,sample):
 node,ct,base=SERVICES[name]
 root='/media/james-bond' if ct==106 else '/media/3 Folder Emby/James Bond'
 command(node,['pct','exec',str(ct),'--','timeout','12','python3','-c',READ_CODE,root,sample])
 if name=='emby':
  # Verify the Docker bind as used by Emby too, not just the LXC namespace.
  path='/mnt/3 Folder Emby/James Bond/'+sample
  command(node,['pct','exec',str(ct),'--','docker','exec','emby','sh','-c','test "$(head -c 4096 "$1" | wc -c)" -gt 0','probe',path])
  info=json.loads(fetch(base+'/System/Info/Public'))
  if not info.get('Version'):raise RuntimeError('invalid Emby API response')
  return {'api':True,'media_read':True}
 return hls(base)
def run():
 STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
 with open(STATE/'lock','w') as lock:
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return {'ok':True,'skipped':'locked','notify':False}
  path=STATE/'state.json'
  state=json.loads(path.read_text()) if path.exists() else {}
  now=time.time();hosts={n:probe(lambda n=n:host_read(n)) for n in ('pc6','pc9')}
  emby=probe(lambda:json.loads(fetch(SERVICES['emby'][2]+'/System/Info/Public')))
  results={};actions=[]
  # Verify current identities on every invocation; fail closed on moves/renumbering.
  inventory=json.loads(command('pc6',['pvesh','get','/cluster/resources','--type','vm','--output-format','json']))
  for name,(node,ct,base) in SERVICES.items():
   identity=any(v.get('vmid')==ct and v.get('node')==node and v.get('status')=='running' and v.get('name')=={200:'ct151-emby',250:'ct162-tunarr',106:'ct106-tunarr'}[ct] for v in inventory)
   dep=hosts[node]['ok'] and identity and (name=='emby' or (emby['ok'] and results.get('emby',{}).get('ok',False)))
   result=probe(lambda:guest_probe(name,hosts[node]['detail'])) if hosts[node]['ok'] and identity else {'ok':False,'detail':'host dependency or identity unavailable'}
   s=state.setdefault(name,{})
   decision=decide(s,result['ok'],dep,now)
   if decision=='repair' and actions:decision='deferred-one-repair-per-run'
   if decision=='repair':
    # Fresh dependency/identity check before each single guest reboot.
    attempts=[t for t in s.get('attempts',[]) if now-t<86400]
    if len(attempts)>=2:decision='max-attempts'
    elif attempts and now-attempts[-1]<1800:decision='cooldown'
    else:
     fresh=probe(lambda:host_read(node))
     current=json.loads(command('pc6',['pvesh','get','/cluster/resources','--type','vm','--output-format','json']))
     still_target=any(v.get('vmid')==ct and v.get('node')==node and v.get('status')=='running' and v.get('name')=={200:'ct151-emby',250:'ct162-tunarr',106:'ct106-tunarr'}[ct] for v in current)
     upstream=name=='emby' or probe(lambda:guest_probe('emby',hosts['pc6']['detail']))['ok']
     if not fresh['ok'] or not still_target or not upstream:decision='blocked'
     else:
      s['attempts']=attempts+[now]
      save(path,state) # Count even failed reboot requests; survive crashes.
      repair=probe(lambda:command(node,['pct','reboot',str(ct)],100))
      actions.append({'service':name,'reboot':repair})
      if repair['ok']:
       until=time.monotonic()+100
       while time.monotonic()<until:
        time.sleep(5);result=probe(lambda:guest_probe(name,fresh['detail']))
        if result['ok']:break
      decision='recovered' if result['ok'] else 'repair-failed'
   results[name]={**result,'decision':decision,'failures':s['failures']}
  ok=all(x['ok'] for x in results.values())
  notify=bool(actions) or (not ok and (now-state.get('_last_notice',0)>=3600)) or (ok and state.get('_down',False))
  if notify:state['_last_notice']=now
  state['_down']=not ok;state['_last_check']=now
  report={'ok':ok,'hosts':hosts,'services':results,'actions':actions,'notify':notify,'at':now}
  save(path,state);save(STATE/'latest.json',report)
  with open(STATE/'events.jsonl','a') as f:f.write(json.dumps(report)+'\n')
  return report

def save(path,data):
 tmp=path.with_suffix('.tmp')
 with open(tmp,'w') as f:
  os.chmod(tmp,0o600);f.write(json.dumps(data,indent=2));f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
 directory=os.open(path.parent,os.O_RDONLY)
 try:os.fsync(directory)
 finally:os.close(directory)
if __name__=='__main__':
 try:print(json.dumps(run()))
 except Exception as e:print(json.dumps({'ok':False,'notify':True,'error':str(e)[:250]}))
