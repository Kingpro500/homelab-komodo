"""Fixed media recovery adapter for the authenticated audit endpoint."""
import json,subprocess

def check():
 result=subprocess.run(['ssh','-i','/home/hermes/.ssh/id_ed25519_media_recovery','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','root@10.0.0.120','/usr/local/sbin/n8n-tower-media-repair'],capture_output=True,text=True,timeout=580)
 if result.returncode:raise RuntimeError('media runner SSH failed: '+result.stderr[-180:])
 return json.loads(result.stdout)
