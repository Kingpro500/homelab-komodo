#!/usr/bin/env python3
"""Drift-vakt for homelab-et.

Finner arbeid som er committet/merget, men ikke publisert/deployet, og
ufullført Git-arbeid som blir liggende. Den STOPPER INGENTING. Den lager:

  * ~/.hermes/state/drift.json  -> vises via GET http://10.0.0.135:9118/drift
                                   og som stor advarsel øverst i nettverkskartet
  * push via n8n `homelab-alerts` ved NYE kritiske funn, én daglig påminnelse
    (fra kl. 09) så lenge noe er kritisk, og [LØST] når alt er ryddet.
    Aldri push mellom 23:00 og 06:00.

Kilde: GitHub Kingpro500/homelab-komodo, pc7-ct130-hermes/drift-vakt/.
Rutine: pc7-ct130-hermes/drift-vakt/README.md. Logger aldri tokens.

    python3 homelab_drift_check.py              # vanlig kjøring (timer)
    python3 homelab_drift_check.py --print      # skriv resultatet til stdout
    python3 homelab_drift_check.py --no-notify  # ingen push
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ENVFILE = os.path.expanduser("~/.hermes/.env")
STATE_DIR = os.path.expanduser("~/.hermes/state")
OUT = os.path.join(STATE_DIR, "drift.json")
MEM = os.path.join(STATE_DIR, "drift-notify.json")
REPO = "Kingpro500/homelab-komodo"
DOC = "https://github.com/%s/blob/main/pc7-ct130-hermes/drift-vakt/README.md" % REPO
N8N = "http://10.0.0.119:5678/webhook/homelab-alerts"
CT120_JSON = "http://10.0.0.124:3020/nettkart-drift.json"
LOCAL_CLONES = [os.path.expanduser("~/homelab-komodo")]
TZ = ZoneInfo("Europe/Oslo")
QUIET_FROM, QUIET_TO = 23, 6
REMIND_HOUR = 9
PR_MAX_HOURS = 24
BRANCH_MAX_DAYS = 3

# Bevisst satt på pause av Roger: vises som «kjent» (grått), gir ikke push.
# Fjern linjen her (i GitHub) når pausen er over.
KNOWN = {
    "stack:pc6-ct120-homepage": "Homepage-arbeid satt på pause av Roger 8. nov (AGENTS.md)",
    "stack:pc6-ct109-dashy": "Dashy-arbeid satt på pause av Roger 8. nov (AGENTS.md)",
}


def load_env(path=ENVFILE):
    env = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return env


ENV = load_env()
ISSUES = []


def issue(key, level, area, title, detail="", fix=""):
    if key in KNOWN and level in ("kritisk", "advarsel"):
        detail = (KNOWN[key] + ". " + detail).strip()
        level = "kjent"
    ISSUES.append({"key": key, "level": level, "area": area, "title": title,
                   "detail": detail, "fix": fix})


def http_json(url, data=None, headers=None, timeout=20):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Accept": "application/json"}
    if body is not None:
        h["Content-Type"] = "application/json"
    h.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def gh(path):
    return http_json("https://api.github.com" + path, headers={
        "Authorization": "Bearer " + ENV.get("GITHUB_TOKEN", ""),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"})


def komodo(typ, params=None):
    base = ENV.get("KOMODO_ADDRESS", "http://10.0.0.117:9120").rstrip("/")
    return http_json("%s/read/%s" % (base, typ), data=params or {}, headers={
        "X-Api-Key": ENV.get("KOMODO_API_KEY", ""),
        "X-Api-Secret": ENV.get("KOMODO_API_SECRET", "")})


def age_hours(iso):
    t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - t).total_seconds() / 3600


# --------------------------------------------------------------------------- GitHub
def check_github():
    access = {"ok": False, "route": "Hermes CT130 (~/.hermes/.env GITHUB_TOKEN) -> api.github.com; "
              "git-push: pc6 /root/claude-work/homelab-komodo med deploy-nøkkel /root/.ssh/claude_github_deploy",
              "checked": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        gh("/repos/" + REPO)
        main_sha = gh("/repos/%s/commits/main" % REPO)["sha"]
        access["ok"] = True
    except Exception as exc:  # noqa: BLE001
        issue("github:access", "kritisk", "GitHub",
              "GitHub-API svarer ikke fra Hermes CT130 (%s)" % type(exc).__name__,
              str(exc)[:200], "Sjekk GITHUB_TOKEN i ~/.hermes/.env på CT130 og nettverk/DNS ut fra CT130.")
        return access, None

    try:
        gh("/repos/%s/contents/docs/network-map?ref=main" % REPO)
        issue("github:map-copy", "kritisk", "GitHub",
              "docs/network-map finnes i GitHub main — kartet skal KUN ligge i Gitea", "",
              "Fjern mappen fra GitHub i én PR. Rett kartet i Gitea-kilden på CT120.")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            issue("github:map-copy-check", "advarsel", "GitHub",
                  "Kunne ikke sjekke om docs/network-map finnes i GitHub (HTTP %d)" % exc.code, "", "")

    for pr in gh("/repos/%s/pulls?state=open&per_page=100" % REPO):
        h = age_hours(pr["created_at"])
        if h >= PR_MAX_HOURS:
            issue("pr:%d" % pr["number"], "advarsel", "GitHub",
                  "Åpen PR #%d i %d døgn: %s" % (pr["number"], h // 24, pr["title"][:80]),
                  pr["html_url"], "Merge og deploy, eller lukk den. Ikke lag en ny PR oppå.")

    stale = []
    for br in gh("/repos/%s/branches?per_page=100" % REPO):
        name = br["name"]
        if name == "main":
            continue
        cmp = gh("/repos/%s/compare/main...%s" % (REPO, urllib.parse.quote(name, safe="")))
        prs = gh("/repos/%s/pulls?state=all&head=%s:%s&per_page=5" % (
            REPO, REPO.split("/")[0], urllib.parse.quote(name, safe="")))
        merged = any(p.get("merged_at") for p in prs)
        open_pr = any(p["state"] == "open" for p in prs)
        commit_age_d = age_hours(cmp["commits"][-1]["commit"]["committer"]["date"]) / 24 if cmp.get("commits") else 999
        if cmp.get("ahead_by", 0) == 0 or merged or (prs and not open_pr):
            stale.append(name)
        elif not open_pr and commit_age_d >= BRANCH_MAX_DAYS:
            issue("branch:" + name, "advarsel", "GitHub",
                  "Grenen %s har %d commit(s) som ikke er i main, uten PR (%d døgn gammel)"
                  % (name, cmp["ahead_by"], commit_age_d), "",
                  "Lag PR og merge, eller spør Roger om grenen skal forkastes.")
    if stale:
        issue("branches:stale", "kjent", "GitHub",
              "%d ferdige/forlatte grener kan ryddes: %s" % (len(stale), ", ".join(sorted(stale))),
              "", "Spør Roger før noe slettes.")
    return access, main_sha


# --------------------------------------------------------------------------- Komodo
def check_komodo(main_sha):
    try:
        stacks = komodo("ListStacks")
    except Exception as exc:  # noqa: BLE001
        issue("komodo:access", "kritisk", "Komodo", "Komodo-API svarer ikke (%s)" % type(exc).__name__,
              str(exc)[:200], "Sjekk Komodo Core CT110 på pc8 (10.0.0.117:9120).")
        return
    cmp_cache = {}
    for s in stacks:
        info = s.get("info", {})
        name = s["name"]
        if info.get("repo") != REPO or info.get("branch") != "main":
            continue
        try:
            full = komodo("GetStack", {"stack": s["id"]})
        except Exception:  # noqa: BLE001
            continue
        cfg, finfo = full.get("config", {}), full.get("info", {})
        if finfo.get("remote_errors"):
            issue("stack-err:" + name, "advarsel", "Komodo",
                  "Stack %s: Komodo får feil ved lesing av filer fra GitHub" % name,
                  json.dumps(finfo["remote_errors"])[:200], "Les Komodo-oppdateringsloggen for stacken og rett stien.")
        deployed = info.get("deployed_hash") or finfo.get("deployed_hash")
        if not deployed or not main_sha:
            continue
        rd = (cfg.get("run_directory") or "").strip("./")
        prefixes = set()
        for fp in cfg.get("file_paths") or []:
            p = "/".join(x for x in (rd, fp) if x)
            prefixes.add(p.rsplit("/", 1)[0] + "/" if "/" in p else p)
        if rd:
            prefixes.add(rd + "/")
        if not prefixes:
            continue
        if deployed not in cmp_cache:
            try:
                cmp_cache[deployed] = gh("/repos/%s/compare/%s...%s" % (REPO, deployed, main_sha))
            except Exception:  # noqa: BLE001
                cmp_cache[deployed] = None
        c = cmp_cache[deployed]
        if not c:
            issue("stack-hash:" + name, "advarsel", "Komodo",
                  "Stack %s: deployet commit %s finnes ikke i GitHub-historikken" % (name, deployed), "",
                  "Kjør PullStack + DeployStack og verifiser deployed_hash.")
            continue
        # Ren dokumentasjon (README/.md, docs/) påvirker ikke en deploy og teller ikke.
        changed = [f["filename"] for f in c.get("files", [])
                   if any(f["filename"].startswith(p) for p in prefixes)
                   and not f["filename"].lower().endswith(".md") and "/docs/" not in "/" + f["filename"]]
        if changed:
            issue("stack:" + name, "kritisk", "Komodo",
                  "Stack %s: endringer merget i main er IKKE deployet (deployet %s, main %s)"
                  % (name, deployed[:7], main_sha[:7]),
                  "Filer: " + ", ".join(changed[:6]) + (" …" if len(changed) > 6 else ""),
                  "Komodo: PullStack + DeployStack for %s, verifiser deployed_hash == latest_hash." % name)


# --------------------------------------------------------------------------- Kartkilden (CT120)
def check_map():
    try:
        d = http_json(CT120_JSON, timeout=10)
    except Exception as exc:  # noqa: BLE001
        issue("map:check", "advarsel", "Nettverkskart",
              "Kartkilde-sjekken på CT120 svarer ikke (%s)" % type(exc).__name__, CT120_JSON,
              "Sjekk /etc/cron.d/nettkart-drift og /usr/local/sbin/nettkart-drift på CT120.")
        return
    if age_hours(d.get("generated", "1970-01-01T00:00:00+00:00")) > 1:
        issue("map:stale", "advarsel", "Nettverkskart", "Kartkilde-sjekken på CT120 er over 1 time gammel", "",
              "Sjekk cron på CT120.")
    for i in d.get("issues", []):
        issue(i["key"], i["level"], "Nettverkskart", i["title"], i.get("detail", ""), i.get("fix", ""))


# --------------------------------------------------------------------------- Lokale kloner
def git(path, *args, timeout=60):
    return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, timeout=timeout)


STORAGE_WARN, STORAGE_CRIT = 80.0, 90.0
STORAGE_SKIP = {"nfs", "cifs", "pbs"}  # NFS dekkes av n8n «Lagring – full-fremskrivning»


def check_storage():
    """Node-lagring (lvmthin `local-lvm`, `local` m.fl.) via Proxmox-API. Advarsel >=80 %, kritisk >=90 %."""
    base = ENV.get("PROXMOX_URL", "").rstrip("/")
    if not base:
        return
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(base + "/api2/json/cluster/resources?type=storage", headers={
        "Authorization": "PVEAPIToken=%s=%s" % (ENV.get("PROXMOX_TOKEN_ID", ""), ENV.get("PROXMOX_TOKEN_SECRET", ""))})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            rows = json.load(r)["data"]
    except Exception as exc:  # noqa: BLE001
        issue("storage:api", "advarsel", "Lagring", "Proxmox-API svarer ikke for lagringssjekk", str(exc)[:200],
              "Sjekk PROXMOX_URL/token i Hermes .env og at pc8 (10.0.0.102) er oppe.")
        return
    for s in rows:
        if s.get("plugintype") in STORAGE_SKIP or not s.get("maxdisk"):
            continue
        pct = 100.0 * s["disk"] / s["maxdisk"]
        if pct < STORAGE_WARN:
            continue
        free = (s["maxdisk"] - s["disk"]) / 1e9
        lvl = "kritisk" if pct >= STORAGE_CRIT else "advarsel"
        note = " Thin-pool kan gå full og stoppe alle gjester på noden." if s.get("plugintype") == "lvmthin" else ""
        issue("storage:%s:%s" % (s["node"], s["storage"]), lvl, "Lagring",
              "%s/%s er %.0f %% full (%.1f GB ledig)" % (s["node"], s["storage"], pct, free),
              "Terskler: advarsel %.0f %%, kritisk %.0f %%.%s" % (STORAGE_WARN, STORAGE_CRIT, note),
              "Frigjør plass (gamle snapshots, ubrukte disker/ISO) eller utvid. Slett ikke gjestedisker uten å spørre Roger.")


def check_clones():
    for path in LOCAL_CLONES:
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        host = "CT130:" + path.replace(os.path.expanduser("~"), "~")
        git(path, "fetch", "-q", "origin", "main")
        branch = git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        dirty = [l for l in git(path, "status", "--porcelain").stdout.splitlines() if l.strip()]
        behind = git(path, "rev-list", "--count", "HEAD..origin/main").stdout.strip() or "0"
        ahead = git(path, "rev-list", "--count", "origin/main..HEAD").stdout.strip() or "0"
        if dirty:
            issue("clone-dirty:" + host, "advarsel", "Git-kloner",
                  "%s har %d ucommittede endringer (gren %s)" % (host, len(dirty), branch),
                  ", ".join(l[3:] for l in dirty[:6]),
                  "Commit + PR det som skal beholdes, ellers spør Roger. Ikke la det ligge.")
        if branch != "main" or int(behind) > 0 or int(ahead) > 0:
            issue("clone-drift:" + host, "advarsel", "Git-kloner",
                  "%s står på gren %s, %s bak og %s foran main" % (host, branch, behind, ahead), "",
                  "Få ev. egne commits inn via PR, deretter `git switch main && git pull --ff-only`.")


# --------------------------------------------------------------------------- Varsling
def push(status, summary, description):
    payload = {"status": status, "job": "drift-vakt", "alerts": [{
        "status": status,
        "labels": {"alertname": "HomelabDrift", "severity": "critical", "node": "pc7-ct130"},
        "annotations": {"summary": summary, "description": description}}]}
    try:
        http_json(N8N, data=payload, timeout=15)
        return True
    except Exception as exc:  # noqa: BLE001
        print("push feilet: %s" % exc, file=sys.stderr)
        return False


def notify(result):
    try:
        with open(MEM, encoding="utf-8") as fh:
            mem = json.load(fh)
    except (OSError, ValueError):
        mem = {"notified": [], "last_remind": ""}
    now = datetime.now(TZ)
    if now.hour >= QUIET_FROM or now.hour < QUIET_TO:
        return
    today = now.date().isoformat()
    crit = {i["key"]: i for i in result["issues"] if i["level"] == "kritisk"}
    new = sorted(set(crit) - set(mem.get("notified", [])))
    lines = "; ".join(i["title"] for i in list(crit.values())[:5])
    if new:
        if push("firing", "STOR ADVARSEL: %d drift-avvik i homelab" % len(crit),
                lines + ". Rydd opp før nytt arbeid. Se nettverkskartet."):
            mem.update(notified=sorted(crit), last_remind=today)
    elif crit and now.hour >= REMIND_HOUR and mem.get("last_remind") != today:
        if push("firing", "Påminnelse: %d drift-avvik ligger fortsatt" % len(crit), lines):
            mem.update(notified=sorted(crit), last_remind=today)
    elif not crit and mem.get("notified"):
        if push("resolved", "Drift-vakt: alt er ryddet", "Ingen kritiske drift-avvik igjen."):
            mem.update(notified=[])
    else:
        mem["notified"] = sorted(set(mem.get("notified", [])) & set(crit))
    with open(MEM, "w", encoding="utf-8") as fh:
        json.dump(mem, fh)


def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    access, main_sha = check_github()
    check_komodo(main_sha)
    check_map()
    check_clones()
    check_storage()
    order = {"kritisk": 0, "advarsel": 1, "kjent": 2}
    ISSUES.sort(key=lambda i: (order.get(i["level"], 9), i["area"], i["key"]))
    levels = {i["level"] for i in ISSUES}
    result = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "level": "kritisk" if "kritisk" in levels else "advarsel" if "advarsel" in levels else "ok",
        "counts": {k: sum(1 for i in ISSUES if i["level"] == k) for k in order},
        "github_access": access,
        "doc": DOC,
        "issues": ISSUES,
    }
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)
    if "--print" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    if "--no-notify" not in sys.argv:
        notify(result)


if __name__ == "__main__":
    main()
