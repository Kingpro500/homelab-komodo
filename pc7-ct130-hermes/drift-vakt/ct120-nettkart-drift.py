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

result = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "source": SRC, "issues": issues}
tmp = OUT + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=1)
os.chmod(tmp, 0o644)
os.replace(tmp, OUT)
