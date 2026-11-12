#!/usr/bin/env python3
"""Drift-vakt, kartdelen. Kjører på CT120 (cron hvert 10. min, /etc/cron.d/nettkart-drift).

Installeres som /usr/local/sbin/nettkart-drift. Skriver nettkart-drift.json i
den levende kartmappen, slik at Hermes (homelab_drift_check.py) og kartet kan
lese den over HTTP. Endrer ingenting i Git og stopper ingenting.

Kilde: GitHub Kingpro500/homelab-komodo, pc7-ct130-hermes/drift-vakt/.
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

SRC = "/opt/moved-services/nettkart-repo"          # Gitea-kilden (eneste kartkilde)
LIVE_DIR = "/srv/nettkart/www"          # nginx-webrot, utenfor alle Git-kopier
KOMODO_CHECKOUT = "/opt/komodo/stacks/pc6-ct120-web"
OUT = os.path.join(LIVE_DIR, "nettkart-drift.json")
issues = []


def git(*args, cwd=SRC):
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=60)


def add(key, level, title, detail="", fix=""):
    issues.append({"key": key, "level": level, "title": title, "detail": detail, "fix": fix})


branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
if branch != "main":
    add("map:branch", "kritisk", "Kartkilden på CT120 står på gren %s, ikke main" % branch, SRC,
        "git switch main i %s og få endringene inn via nettkart-publish." % SRC)

dirty = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
if dirty:
    add("map:dirty", "kritisk", "Kartkilden på CT120 har %d ucommittede endringer" % len(dirty),
        ", ".join(l[3:] for l in dirty[:8]),
        "Commit og kjør /usr/local/sbin/nettkart-publish – eller spør Roger om endringen skal forkastes.")

ahead = (git("rev-list", "--count", "origin/main..HEAD").stdout.strip() or "0")
if int(ahead) > 0:
    add("map:unpushed", "kritisk", "Kartkilden på CT120 har %s commit(s) som ikke er pushet/publisert" % ahead,
        git("log", "--oneline", "origin/main..HEAD").stdout.strip()[:300],
        "Kjør /usr/local/sbin/nettkart-publish på CT120.")

head_map = subprocess.run(["git", "-C", SRC, "show", "HEAD:docs/network-map/nettverkskart.html"],
                          capture_output=True, timeout=60).stdout
try:
    with open(os.path.join(LIVE_DIR, "nettverkskart.html"), "rb") as fh:
        live_map = fh.read()
except OSError:
    live_map = b""
if hashlib.sha256(head_map).digest() != hashlib.sha256(live_map).digest():
    add("map:live-differs", "kritisk", "Det publiserte kartet er ikke likt siste commit i kartkilden",
        "live %d byte, commit %d byte" % (len(live_map), len(head_map)),
        "Kjør /usr/local/sbin/nettkart-publish på CT120. Ikke rediger live-mappen direkte.")

# Webroten skal ligge utenfor Komodo-checkouten (flyttet 10. nov 2026).
mount = subprocess.run(["docker", "inspect", "nettkart", "--format",
                        "{{range .Mounts}}{{if eq .Destination \"/usr/share/nginx/html\"}}{{.Source}}{{end}}{{end}}"],
                       capture_output=True, text=True, timeout=30).stdout.strip()
if mount != LIVE_DIR:
    add("map:nginx-mount", "kritisk", "nginx (nettkart) serverer ikke %s, men %s" % (LIVE_DIR, mount or "ukjent"),
        "Det levende kartet kan bli overskrevet fra en Git-kopi.",
        "Deploy pc6-ct120-web fra GitHub main (compose monterer /srv/nettkart/www).")
if os.path.isdir(os.path.join(KOMODO_CHECKOUT, "docs", "network-map")):
    add("map:github-copy", "kritisk", "docs/network-map finnes igjen i Komodo-checkouten (GitHub-kopi av kartet)",
        KOMODO_CHECKOUT + "/docs/network-map",
        "Fjern docs/network-map fra GitHub i én PR. Kartet skal bare ligge i Gitea.")

# Gitea skal KUN inneholde kartet (ryddet 10. nov 2026).
ALLOWED_ROOT = {"README.md", "AGENTS.md", "CLAUDE.md"}
extra = [f for f in git("ls-files").stdout.splitlines()
         if not f.startswith("docs/network-map/") and f not in ALLOWED_ROOT]
if extra:
    add("map:gitea-extra", "kritisk", "Gitea-repoet har %d fil(er) utenfor kartmappen — Gitea skal KUN ha de lokale sidene (kartet og advarselsiden)" % len(extra),
        ", ".join(extra[:8]), "Fjern dem fra Gitea i én commit; det som hører hjemme et sted, skal i GitHub.")

# Webroten skal bare ha det nettkart-publish og kartets tjenester legger der.
# Alt som ligger i kartmappen i Gitea hører hjemme i webroten; i tillegg kommer
# filene tjenestene på CT120 genererer selv. Slik gir en ny kartside ikke falsk alarm.
ALLOWED_WEB = {"daily-report.json", "nettkart-drift.json", "versions"}
ALLOWED_WEB |= {f.split("/")[-1] for f in git("ls-files", "docs/network-map").stdout.split()
                if f.count("/") == 2}
stray = sorted(f for f in os.listdir(LIVE_DIR) if f not in ALLOWED_WEB and not f.startswith("."))
if stray:
    add("map:webroot-extra", "advarsel", "Ukjente filer i webroten %s" % LIVE_DIR, ", ".join(stray[:8]),
        "Webroten fylles bare av nettkart-publish. Flytt filene ut, eller legg dem i Gitea og publiser.")

# Blokkert publisering: åpne saker meldt med `homelab-blokkert meld` (se README).
BLOCKED_DB = "/var/lib/homelab-blokkert/blokkert.json"
try:
    with open(BLOCKED_DB, encoding="utf-8") as fh:
        blocked = json.load(fh)
except (FileNotFoundError, ValueError):
    blocked = []
for b in blocked:
    if b.get("løst"):
        continue
    add("blokkert:" + b["id"], "kritisk", "⛔ Blokkert publisering: %s" % b["hva"],
        "Meldt %s av %s. Rute prøvd: %s. Feil: %s" % (b["meldt"], b["av"], b["rute"], b["feil"]),
        "Rett ruten og fullfør publiseringen, og kjør så `homelab-blokkert løst %s` på pc6 eller CT120." % b["id"])

result = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "source": SRC, "issues": issues}
tmp = OUT + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)
os.chmod(tmp, 0o644)
os.replace(tmp, OUT)
