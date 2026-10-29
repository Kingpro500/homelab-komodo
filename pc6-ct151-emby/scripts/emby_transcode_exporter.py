#!/usr/bin/env python3
"""Read-only Prometheus exporter for Emby's local FFmpeg processes.
Runs inside CT200; never stops, restarts, or deletes anything.
"""
import os, re, time, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get('PORT', '9121'))

def sample():
    lines = []
    try:
        out = subprocess.check_output(['ps','-eo','pid,pcpu,pmem,etime,args'], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return {'emby_transcode_collector_success': 0}
    jobs=[]
    for row in out.splitlines()[1:]:
        m=re.match
        if not re.search(r'\s(?:/|[A-Za-z0-9_.-]+/)?ffmpeg(?:\s|$)', row):
            continue
        m=re.match(r'\s*(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+(\S+)\s+(.*)', row)
        if not m: continue
        pid,cpu,mem,elapsed,args=m.groups()
        speed=None
        sm=re.search(r'\bspeed=([0-9.]+)x', args)
        if sm: speed=float(sm.group(1))
        overlay=1 if ('overlay' in args or 'hwdownload' in args or 'hwupload' in args) else 0
        jobs.append((pid,float(cpu),float(mem),speed,overlay))
    result={'emby_transcode_collector_success':1,
            'emby_transcode_active_jobs':len(jobs),
            'emby_transcode_cpu_percent':sum(x[1] for x in jobs),
            'emby_transcode_memory_percent':sum(x[2] for x in jobs),
            'emby_transcode_overlay_jobs':sum(x[4] for x in jobs)}
    speeds=[x[3] for x in jobs if x[3] is not None]
    result['emby_transcode_speed_ratio']=min(speeds) if speeds else -1
    for pid,cpu,mem,speed,overlay in jobs:
        labels='{pid="%s"}'%pid
        result['emby_transcode_job_cpu_percent'+labels]=cpu
        result['emby_transcode_job_overlay'+labels]=overlay
        if speed is not None: result['emby_transcode_job_speed_ratio'+labels]=speed
    return result

def render():
    s=sample(); out=[]
    for k,v in s.items():
        if k.startswith('#'): continue
        name=k.split('{',1)[0]
        if '{' not in k: out.append(f'{k} {v}')
        else: out.append(f'{k} {v}')
    return '\n'.join(out)+'\n'

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/metrics': self.send_response(404); self.end_headers(); return
        body=render().encode(); self.send_response(200); self.send_header('Content-Type','text/plain; version=0.0.4'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, format, *args): pass

if __name__=='__main__':
    ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
