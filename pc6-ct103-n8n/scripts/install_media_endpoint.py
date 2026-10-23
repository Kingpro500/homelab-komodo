#!/usr/bin/env python3
"""Idempotent audit-server integration; run as hermes after copying adapter."""
from pathlib import Path
p=Path('/home/hermes/.hermes/scripts/homelab_audit_server.py')
s=p.read_text()
old='"/emby/status", "/emby/restart", "/openrouter/spend",'
new='"/emby/status", "/emby/restart", "/media/check", "/openrouter/spend",'
marker='        if path in ("/dns/status", "/dns/reconcile"):'
block='''        if path == "/media/check":
            if self.command != "POST":
                self._send(405, json.dumps({"error": "use POST"}))
                return
            try:
                import media_recovery_adapter
                payload = media_recovery_adapter.check()
                self._send(200, json.dumps(payload))
            except Exception as e:
                self._send(502, json.dumps({"ok": False, "notify": True, "error": str(e)[:250]}))
            return

'''
if 'if path == "/media/check":' in s:
 assert new in s
 print('media endpoint already installed')
else:
 assert s.count(old)==1 and s.count(marker)==1, 'Unexpected audit server version; inspect manually'
 backup=p.with_suffix('.py.before-media')
 if not backup.exists():backup.write_text(s);backup.chmod(0o600)
 s=s.replace(old,new).replace(marker,block+marker)
 compile(s,str(p),'exec');p.write_text(s)
 print('media endpoint installed; restart homelab-audit')
