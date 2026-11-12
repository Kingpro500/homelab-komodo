"""Read-only Emby playback/transcode snapshot for the audit adapter."""
import json
import re
import subprocess
import time

KEY = "/home/hermes/.ssh/id_ed25519_hermes"
HOST = "root@10.0.0.120"


def ssh(command, timeout=30):
    return subprocess.run(
        ["ssh", "-i", KEY, "-o", "BatchMode=yes",
         "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=8",
         HOST, command], capture_output=True, text=True, timeout=timeout
    )


def parse_path(text):
    match = re.search(r'\{"Chapters".*\}', text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def snapshot():
    listing = ssh("pct exec 200 -- docker exec emby sh -c 'find /config/logs -type f -name ffmpeg-transcode-*.txt -exec ls -t {} \\; | head -8'")
    names = re.findall(r"ffmpeg-transcode-[0-9a-f-]+_1\.txt", listing.stdout)
    jobs = []
    for name in names[:6]:
        command = (
            "pct exec 200 -- docker exec emby sh -c "
            "'grep -a -m1 Path /config/logs/%s; "
            "grep -a speed= /config/logs/%s | tail -1; "
            "grep -a ThrottleBuffer /config/logs/%s | tail -1'"
            % (name, name, name)
        )
        result = ssh(command)
        text = result.stdout
        path = parse_path(text)
        speeds = re.findall(r"speed=\s*([0-9.]+)x", text)
        buffers = re.findall(r"ThrottleBuffer: (-?[0-9]+)s", text)
        jobs.append({
            "log": name,
            "path": (path or {}).get("Path"),
            "speed": float(speeds[-1]) if speeds else None,
            "throttle_buffer_s": int(buffers[-1]) if buffers else None,
            "read_ok": result.returncode == 0,
            "sampled_at": time.time(),
        })
    return {"jobs": jobs, "job_count": len(jobs), "read_only": True, "sampled_at": time.time()}
