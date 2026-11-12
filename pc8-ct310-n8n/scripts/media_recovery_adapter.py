"""Fixed media recovery adapter for the authenticated audit endpoint."""
import json
import subprocess


def _ssh(command, timeout=580):
    return subprocess.run(
        [
            "ssh", "-i", "/home/hermes/.ssh/id_ed25519_media_recovery",
            "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", "ConnectTimeout=8", "root@10.0.0.120", command,
        ], capture_output=True, text=True, timeout=timeout
    )


def check():
    result = _ssh("/usr/local/sbin/n8n-tower-media-repair")
    if result.returncode:
        raise RuntimeError("media runner SSH failed: " + result.stderr[-180:])
    payload = json.loads(result.stdout)
    try:
        from media_performance_adapter import snapshot
        payload["playback_performance"] = snapshot()
    except Exception as exc:
        payload["playback_performance"] = {
            "read_only": True,
            "ok": False,
            "error": str(exc)[:250],
        }
    payload["performance_policy"] = {
        "speed_risk_below": 1.0,
        "speed_warn_below": 1.15,
        "min_samples": 2,
        "restart_allowed": False,
    }
    return payload
