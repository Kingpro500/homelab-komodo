#!/usr/bin/env python3
"""Observe Emby offline Download & Sync jobs and notify through Home Assistant.

This is deliberately a read-only Emby integration.  It polls the documented
Sync endpoints, sends transition notifications and retains only job IDs,
status and progress in its state file.  Titles, user names and target names
are resolved for the notification itself and are never written to disk or
stdout.

It observes Emby's Download & Sync jobs.  A browser's ordinary direct file
download is not represented by a Sync job and cannot reliably be inferred
from this API.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


HOME = Path("/home/hermes")
ENVFILE = Path(os.environ.get("HOMELAB_ENVFILE", HOME / ".hermes" / ".env"))
STATE_FILE = Path(os.environ.get(
    "EMBY_SYNC_STATE_FILE", HOME / ".hermes" / "data" / "emby_sync_state.json"
))
EMBY_HOST = os.environ.get("EMBY_HOST", "10.0.0.150")
EMBY_PORT = int(os.environ.get("EMBY_PORT", "8096"))
TIMEOUT_S = int(os.environ.get("EMBY_SYNC_TIMEOUT_S", "12"))
DEFAULT_NOTIFY_TARGET = "mobile_app_1_iphone_r"
TERMINAL = {"Completed", "CompletedWithError", "Failed"}


def load_env() -> dict[str, str]:
    values = dict(os.environ)
    try:
        for raw in ENVFILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values.setdefault(key.strip(), value.strip().strip("\"'") )
    except OSError:
        pass
    return values


def api(env: dict[str, str], path: str) -> Any:
    key = env.get("EMBY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("missing Emby API key")
    request = urllib.request.Request(
        f"http://{EMBY_HOST}:{EMBY_PORT}{path}",
        headers={"X-Emby-Token": key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"Emby Sync API failed: {type(exc).__name__}") from exc


def load_state() -> dict[str, Any]:
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if payload.get("schema") == 1 and isinstance(payload.get("jobs"), dict):
            return payload
    except (OSError, ValueError, TypeError):
        pass
    return {"schema": 1, "initialized": False, "jobs": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".emby-sync-", dir=STATE_FILE.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, STATE_FILE)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def query_items(env: dict[str, str], target_id: str) -> list[dict[str, Any]]:
    encoded = urllib.parse.quote(target_id, safe="")
    payload = api(env, f"/Sync/JobItems?TargetId={encoded}")
    return payload.get("Items", []) if isinstance(payload, dict) else []


def user_name(env: dict[str, str], user_id: Any) -> str:
    if user_id in (None, ""):
        return "ukjent bruker"
    try:
        payload = api(env, "/Users/" + urllib.parse.quote(str(user_id), safe=""))
        return str(payload.get("Name") or "ukjent bruker")
    except RuntimeError:
        return "ukjent bruker"


def job_details(env: dict[str, str], job: dict[str, Any]) -> tuple[str, str]:
    """Return ephemeral user and title text; never put either in persistent state."""
    owner = user_name(env, job.get("UserId"))
    names: list[str] = []
    target_id = str(job.get("TargetId") or "")
    if target_id:
        try:
            for item in query_items(env, target_id):
                if str(item.get("JobId")) == str(job.get("Id")):
                    name = str(item.get("ItemName") or "").strip()
                    if name and name not in names:
                        names.append(name)
        except RuntimeError:
            pass
    label = ", ".join(names[:3])
    if len(names) > 3:
        label += f" (+{len(names) - 3})"
    return owner, (label or str(job.get("Name") or "ukjent tittel"))


def notify(env: dict[str, str], title: str, message: str, tag: str) -> None:
    base = env.get("HASS_URL", "").rstrip("/")
    token = env.get("HASS_TOKEN", "")
    target = env.get("EMBY_SYNC_NOTIFY_TARGET", DEFAULT_NOTIFY_TARGET).strip()
    if not base or not token or not target:
        raise RuntimeError("Home Assistant notification configuration missing")
    body = json.dumps({
        "title": title,
        "message": message,
        "data": {"tag": tag, "channel": "Emby"},
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/services/notify/{target}",
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            if response.status != 200:
                raise RuntimeError("Home Assistant notification failed")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Home Assistant notification failed: {type(exc).__name__}") from exc


def message_for(job: dict[str, Any], owner: str, item_title: str) -> str:
    target = str(job.get("TargetName") or job.get("TargetId") or "ukjent enhet")
    status = str(job.get("Status") or "ukjent")
    progress = job.get("Progress")
    suffix = f" · {status}"
    if isinstance(progress, (int, float)):
        suffix += f" · {progress:.0f}%"
    return f"{item_title} · {owner} · {target}{suffix}"


def event(env: dict[str, str], kind: str, job: dict[str, Any]) -> None:
    owner, item_title = job_details(env, job)
    labels = {
        "started": "Emby-nedlasting startet",
        "finished": "Emby-nedlasting ferdig",
        "failed": "Emby-nedlasting feilet",
        "stopped": "Emby-nedlasting stoppet",
    }
    notify(env, labels[kind], message_for(job, owner, item_title), "emby-sync-" + str(job.get("Id")))


def snapshot(job: dict[str, Any]) -> dict[str, Any]:
    """Only non-personal, non-title job state is persisted."""
    return {
        "status": str(job.get("Status") or "unknown"),
        "progress": float(job.get("Progress") or 0),
        "target_id": str(job.get("TargetId") or ""),
        "seen_at": int(time.time()),
    }


def main() -> int:
    env = load_env()
    payload = api(env, "/Sync/Jobs")
    jobs = payload.get("Items", []) if isinstance(payload, dict) else []
    jobs = [job for job in jobs if isinstance(job, dict) and job.get("Id") is not None]
    state = load_state()
    current = {str(job["Id"]): job for job in jobs}

    # First execution is a baseline. Existing work must never produce a burst.
    if not state.get("initialized"):
        state["initialized"] = True
        state["jobs"] = {job_id: snapshot(job) for job_id, job in current.items()}
        save_state(state)
        return 0

    previous: dict[str, dict[str, Any]] = state.get("jobs", {})
    next_state: dict[str, dict[str, Any]] = {}
    for job_id, job in current.items():
        prior = previous.get(job_id)
        status = str(job.get("Status") or "unknown")
        if prior is None:
            event(env, "started", job)
        elif prior.get("status") != status:
            if status == "Completed":
                event(env, "finished", job)
            elif status in {"CompletedWithError", "Failed"}:
                event(env, "failed", job)
        next_state[job_id] = snapshot(job)

    # A non-terminal job removed from Emby without a terminal transition was
    # cancelled/removed. We have no title at this point and intentionally send
    # no generic message rather than persist a title solely for this case.
    state["jobs"] = next_state
    save_state(state)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Do not put user/title/API response content in the system journal.
        print(f"emby sync monitor error: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
