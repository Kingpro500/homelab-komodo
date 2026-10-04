#!/usr/bin/env python3
"""Sjekk homepage/config/services.yaml mot virkeligheten i Proxmox.

Finner feil i IP-adresser, CT-/VM-nummer og node-plassering.
"""
import json
import os
import re
import subprocess
import urllib.request
import ssl

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES = REPO + "/homepage/config/services.yaml"

# Proxmox credentials: environment first, then a dotenv-style file.
#   PROXMOX_URL, PROXMOX_TOKEN_ID, PROXMOX_TOKEN_SECRET
ENVFILE = os.environ.get(
    "HOMELAB_ENVFILE",
    os.path.expanduser("~/.hermes/.env"),
)


def load_env(path):
    vals = {}
    if not os.path.exists(path):
        return vals
    for line in open(path):
        if "=" in line and not line.startswith("#"):
            k, v = line.rstrip("\n").split("=", 1)
            vals[k] = v.strip().strip('"')
    return vals


env = dict(os.environ)
for k, v in load_env(ENVFILE).items():
    env.setdefault(k, v)

BASE = env["PROXMOX_URL"].rstrip("/")
TOKEN = env["PROXMOX_TOKEN_ID"] + "=" + env["PROXMOX_TOKEN_SECRET"]
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def api(path):
    req = urllib.request.Request(
        BASE + "/api2/json/" + path, headers={"Authorization": "PVEAPIToken=" + TOKEN})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=12) as r:
            return json.loads(r.read())["data"]
    except Exception:
        return {}


real = {}
for node in ["pc1", "pc6", "pc9", "pve"]:
    for kind in ("lxc", "qemu"):
        for g in api(f"nodes/{node}/{kind}"):
            cfg = api(f"nodes/{node}/{kind}/{g['vmid']}/config")
            if not isinstance(cfg, dict):
                continue
            name = cfg.get("hostname") or cfg.get("name") or ""
            net = cfg.get("net0") or ""
            if not isinstance(net, str):
                net = json.dumps(net)
            for ip in re.findall(r"ip=([0-9.]+)", net):
                real[ip] = (node, g["vmid"], name, g["status"])

real["10.0.0.101"] = ("pc6", 101, "Unraid-Tower", "running")
real["10.0.0.1"] = ("router", None, "OPNsense", "running")

# Proxmox nodes are not guests: they live in /nodes/<name>/status, so record
# them separately to avoid reporting every node link as an unknown IP.
# Proxmox nodes are not guests. /nodes/<n>/status has no "status" field, so use
# cluster/resources?type=node for liveness and /nodes/<n>/network for addresses.
nodes = {}
for res in api("cluster/resources?type=node") or []:
    if res.get("node"):
        nodes[res["node"]] = res.get("status", "unknown")

for name, live in nodes.items():
    net = api(f"nodes/{name}/network")
    for iface in net if isinstance(net, list) else []:
        cidr = iface.get("cidr")
        if cidr and iface.get("active"):
            real.setdefault(
                cidr.split("/")[0],
                (name, None, f"node {name}", "running" if live == "online" else live),
            )

# Name aliases: the config says pc8, the API says pve.
ALIAS = {"pc8": "pve"}

text = open(SERVICES).read()
import itertools
SEGMENT = ""
group = None
entries = []
for line in text.splitlines():
    m = re.match(r"^- ([^:]+):\s*$", line)
    if m:
        group = m.group(1)
        continue
    m = re.match(r"^    - ([^:]+):\s*$", line)
    if m and group:
        entries.append([group, m.group(1), None, None, ""])
        continue
    if entries and line.strip().startswith("href:"):
        entries[-1][4] = line.strip()
    m = re.search(r"href:\s*https?://([0-9.]+)(?::(\d+))?", line)
    if m and entries:
        entries[-1][2] = m.group(1) + ((":" + m.group(2)) if m.group(2) else "")
    m = re.search(r"description:\s*(.+)$", line)
    if m and entries and not entries[-1][3]:
        entries[-1][3] = m.group(1).strip()

print(f"Tjenester i services.yaml: {len(entries)}")
print(f"Gjester funnet i Proxmox: {len([v for v in real.values() if v[1]])}\n")

problems = 0
for grp, name, ip, desc, hrefline in entries:
    href = re.search(r"href:\s*(\S+)", text_line_holder[0]) if False else None
    if not ip:
        # eksterne URL-er (play.sonos.com, openrouter.ai) har ingen IP og er OK
        external = re.search(r"https?://(?![0-9])", hrefline)
        if external:
            continue
        print(f"  [Mangler href] {grp} / {name}")
        problems += 1
        continue
    host = ip.rsplit(":", 1)[0]
    if host not in real:
        print(f"  [IP ukjent]   {grp} / {name:20} {ip}")
        problems += 1
        continue
    node, vmid, hname, state = real[host]
    m = re.search(r"·\s*(CT|VM)?(\d+)\s*·\s*(pc\d+)", desc or "")
    if vmid is None:
        # host-level entry (Proxmox node, router, Unraid VM)
        if hname.startswith("node ") and state != "running":
            print(f"  [Node nede]    {grp} / {name:20} {ip:22} {state}")
            problems += 1
        continue
    if m:
        claim_kind = (m.group(1) or "CT").upper()
        claim_id = m.group(2)
        claim_node = m.group(3)
        real_kind = "CT" if vmid and 100 <= int(vmid) < 200 else "CT"
        if vmid is None:
            continue
        if claim_id != str(vmid) or claim_node != node:
            print(f"  [Plassering]  {grp} / {name:20} {ip:22} "
                  f"says {claim_kind}{claim_id}·{claim_node}, "
                  f"actually {real_kind}{vmid}·{node} ({hname})")
            problems += 1
    if state not in ("running",):
        print(f"  [Nede]        {grp} / {name:20} {ip:22} {state}")
        problems += 1

print(f"\nAvvik: {problems}")
