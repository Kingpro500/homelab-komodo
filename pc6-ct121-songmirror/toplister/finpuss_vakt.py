"""Finpuss-vakt: keeps the SongMirror "Finpuss: Spotify -> Apple" job in step with
renames and deletions the user makes in Spotify.

The sync job selects playlists by *name*, and Apple library playlists cannot be
renamed through the API. This watcher tracks the Spotify playlists by *id*:

* rename in Spotify   -> job list updated to the new name; once the sync has
                         created the new Apple playlist, the old-named Apple
                         playlist is deleted.
* delete in Spotify   -> after two consecutive checks without it, the Apple
                         playlist with that name is deleted and the name is
                         dropped from the job.
* new Spotify list whose name starts with a number+letter or letter+number
  (e.g. "9 A Rock", "A9 Rock") -> added to the job.

Safety: no Apple deletions in a cycle where the Spotify library read looks
incomplete, at most MAX_APPLE_DELETES per cycle, and only Apple playlists whose
name was previously tracked are ever deleted.

Env: SONGMIRROR_DATA (/sm, read-only), STATE_DIR (/state), SONGMIRROR_URL
(http://songmirror:8080), JOB_ID, INTERVAL_S (300), DRY_RUN=1 to log only.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

SM = Path(os.getenv("SONGMIRROR_DATA", "/sm"))
STATE = Path(os.getenv("STATE_DIR", "/state")) / "finpuss_vakt.json"
API = os.getenv("SONGMIRROR_URL", "http://songmirror:8080")
JOB_ID = os.getenv("JOB_ID", "9a81dcc0")
INTERVAL = int(os.getenv("INTERVAL_S", "300"))
DRY = os.getenv("DRY_RUN", "0") == "1"
MAX_APPLE_DELETES = 5
PATTERN = re.compile(r"^\s*(\d{1,2}\s?[A-Za-zÆØÅæøå]\b|[A-Za-zÆØÅæøå]\d{1,2}\b)")
AMP = "https://amp-api.music.apple.com/v1"
os.environ.setdefault("SPOTIFY_SP_DC_FILE", str(SM / "spotify_sp_dc.private"))
os.environ.setdefault("SONGMIRROR_DATA_DIR", "/tmp/sm-vakt")

from songmirror.engine import spotify_cookie as sc  # noqa: E402

HDR = {"X-SongMirror-Request": "1", "Content-Type": "application/json"}


def log(*a):
    print(time.strftime("[%Y-%m-%d %H:%M:%S]"), *a, flush=True)


def fold(s):
    return (s or "").strip().casefold()


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"tracked": {}, "missing": {}, "pending_apple_delete": []}


def save_state(st):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1))
    tmp.replace(STATE)


# ------------------------------------------------------------------ songmirror job
def get_job():
    r = requests.get(f"{API}/api/syncs", timeout=30)
    r.raise_for_status()
    data = r.json()
    jobs = data if isinstance(data, list) else data.get("syncs", [])
    for j in jobs:
        if j.get("id") == JOB_ID:
            return j
    raise RuntimeError(f"sync job {JOB_ID} not found")


def put_job_playlists(names):
    if DRY:
        log(f"  [dry] job playlists -> {len(names)}")
        return
    r = requests.put(f"{API}/api/syncs/{JOB_ID}", headers=HDR,
                     data=json.dumps({"playlists": ",".join(names)}), timeout=30)
    r.raise_for_status()


# ------------------------------------------------------------------ apple
def apple_headers():
    env = {}
    for line in (SM / "profiles/profile_default_apple/app.env").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    b = env.get("APPLE_BEARER_TOKEN", "")
    h = {"Authorization": b if b.lower().startswith("bearer") else "Bearer " + b,
         "Origin": "https://music.apple.com"}
    if env.get("APPLE_USER_TOKEN"):
        h["Media-User-Token"] = env["APPLE_USER_TOKEN"]
    return h


def apple_playlists(h):
    out, off = {}, 0
    while True:
        r = requests.get(f"{AMP}/me/library/playlists", params={"limit": 100, "offset": off},
                         headers=h, timeout=30)
        r.raise_for_status()
        j = r.json()
        rows = j.get("data") or []
        for p in rows:
            out.setdefault(fold(p.get("attributes", {}).get("name")), []).append(p)
        if not j.get("next") or not rows:
            return out
        off += len(rows)


def apple_delete(h, playlist):
    name = playlist.get("attributes", {}).get("name")
    if DRY:
        log(f"  [dry] would delete Apple playlist {name!r} ({playlist['id']})")
        return True
    r = requests.delete(f"{AMP}/me/library/playlists/{playlist['id']}", headers=h, timeout=30)
    log(f"  deleted Apple playlist {name!r} -> HTTP {r.status_code}")
    return r.status_code in (200, 202, 204)


# ------------------------------------------------------------------ cycle
def cycle(st):
    job = get_job()
    names = [n for n in (job.get("playlists") or "").split(",") if n.strip()]
    lib = {}
    for p in sc.library_playlists():
        pid = p.get("id") or str(p.get("uri", "")).rsplit(":", 1)[-1]
        lib[pid] = p
    by_name = {}
    for pid, p in lib.items():
        by_name.setdefault(fold(p.get("name")), []).append(pid)
    tracked = st["tracked"]

    # first run / adopt: track every job name that resolves to exactly one Spotify list
    for n in names:
        ids = by_name.get(fold(n), [])
        if len(ids) == 1 and ids[0] not in tracked:
            tracked[ids[0]] = n.strip()
    library_ok = len(lib) >= max(10, int(0.9 * st.get("library_size", 0)))
    st["library_size"] = max(st.get("library_size", 0), len(lib)) if library_ok else st.get("library_size", 0)

    new_names = list(names)
    changed = False
    for pid, old in list(tracked.items()):
        p = lib.get(pid)
        if p is None:
            if not library_ok:
                continue
            st["missing"][pid] = st["missing"].get(pid, 0) + 1
            if st["missing"][pid] >= 2:
                log(f"Spotify list deleted: {old!r}")
                new_names = [n for n in new_names if fold(n) != fold(old)]
                st["pending_apple_delete"].append({"name": old, "after": None})
                tracked.pop(pid)
                st["missing"].pop(pid, None)
                changed = True
            continue
        st["missing"].pop(pid, None)
        cur = (p.get("name") or "").strip()
        if fold(cur) != fold(old):
            if "," in cur:
                log(f"  ! renamed to a name with a comma, can't sync: {cur!r} (rename it without a comma)")
                continue
            log(f"Spotify rename: {old!r} -> {cur!r}")
            new_names = [cur if fold(n) == fold(old) else n for n in new_names]
            if fold(cur) not in map(fold, new_names):
                new_names.append(cur)
            st["pending_apple_delete"].append({"name": old, "after": cur})
            tracked[pid] = cur
            changed = True

    # new matching lists created/renamed in Spotify
    for pid, p in lib.items():
        nm = (p.get("name") or "").strip()
        owned = p.get("owned", p.get("_owned", p.get("_editable", True)))
        if pid in tracked or not owned or not PATTERN.match(nm) or "," in nm:
            continue
        if len(by_name.get(fold(nm), [])) != 1:
            continue
        log(f"new list picked up: {nm!r}")
        tracked[pid] = nm
        if fold(nm) not in map(fold, new_names):
            new_names.append(nm)
        changed = True

    log(f"check: {len(tracked)} tracked, {len(new_names)} in job, library {len(lib)}"
        + ("" if library_ok else " (library read looks incomplete - no deletions)"))
    if changed or [fold(n) for n in new_names] != [fold(n) for n in names]:
        put_job_playlists(new_names)
        log(f"job now has {len(new_names)} playlists")

    # Apple cleanup of old names
    if st["pending_apple_delete"] and library_ok:
        h = apple_headers()
        ap = apple_playlists(h)
        keep, deleted = [], 0
        live = {fold(n) for n in new_names}
        for item in st["pending_apple_delete"]:
            old = fold(item["name"])
            if old in live:  # name is in use again; never delete it
                continue
            if item["after"] and fold(item["after"]) not in ap:
                keep.append(item)  # wait until the sync has created the renamed copy
                continue
            if deleted >= MAX_APPLE_DELETES:
                keep.append(item)
                continue
            for pl in ap.get(old, []):
                if str(pl.get("id", "")).startswith("p.") and apple_delete(h, pl):
                    deleted += 1
        st["pending_apple_delete"] = keep if not DRY else st["pending_apple_delete"]


def main():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    while True:
        st = load_state()
        try:
            cycle(st)
            if not DRY:
                save_state(st)
        except Exception as e:  # noqa: BLE001
            log(f"cycle failed: {e!r}"[:300])
        if os.getenv("ONCE") == "1":
            return
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
