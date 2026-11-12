#!/usr/bin/env python3
"""Pi-hole DNS failover controlled by Hermes."""
import base64
import json
import os
import socket
import ssl
import struct
import time
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Oslo")
ENVFILE = os.environ.get("HOMELAB_ENVFILE", os.path.expanduser("~/.hermes/.env"))
STATE = os.path.expanduser("~/.hermes/scripts/.dns_failover_state.json")
SUBNET_UUID = "560ce33c-4617-4b3c-af80-4fc1d8b8364e"
PIHOLES = ("10.0.0.115", "10.0.0.116")
UNBOUND = "10.0.0.1"
HEALTH_NAME = "homeassistant.lan.local"
FAIL_THRESHOLD = RECOVER_THRESHOLD = 3

def load_env():
    env = dict(os.environ)
    try:
        with open(ENVFILE) as source:
            for line in source:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env.setdefault(key, value.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass
    return env

ENV = load_env()

def _state():
    try:
        with open(STATE) as source:
            data = json.load(source)
            if isinstance(data, dict):
                return data
    except (FileNotFoundError, ValueError, OSError):
        pass
    return {"both_down": 0, "healthy": 0}

def _save(state):
    temp = STATE + ".tmp"
    with open(temp, "w") as target:
        json.dump(state, target, sort_keys=True)
    os.replace(temp, STATE)

def _query(host, qname=HEALTH_NAME, timeout=2):
    labels = qname.rstrip(".").split(".")
    question = b"".join(bytes((len(label),)) + label.encode("ascii") for label in labels) + b"\0"
    query_id = int(time.monotonic_ns() & 0xFFFF)
    packet = struct.pack("!HHHHHH", query_id, 0x0100, 1, 0, 0, 0) + question + struct.pack("!HH", 1, 1)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(packet, (host, 53))
            response, _ = sock.recvfrom(4096)
    except OSError:
        return False
    if len(response) < 12:
        return False
    response_id, flags, questions, answers, _, _ = struct.unpack("!HHHHHH", response[:12])
    return response_id == query_id and questions == 1 and (flags & 0x000F) == 0 and answers > 0

def health():
    return {address: _query(address) for address in PIHOLES}

def _api(method, path, body=None):
    base = (ENV.get("OPNSENSE_URL") or "").rstrip("/")
    key = ENV.get("OPNSENSE_API_KEY") or ""
    secret = ENV.get("OPNSENSE_API_SECRET") or ""
    if not (base and key and secret):
        raise RuntimeError("OPNsense API-konfigurasjon mangler i Hermes .env")
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(base + path, data=payload, method=method)
    token = base64.b64encode((key + ":" + secret).encode()).decode()
    request.add_header("Authorization", "Basic " + token)
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=15, context=ssl._create_unverified_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
        raise RuntimeError("OPNsense API-feil: %s" % error) from error

def configured_dns():
    data = _api("GET", "/api/kea/dhcpv4/get_subnet/" + SUBNET_UUID)
    servers = data.get("subnet4", {}).get("option_data", {}).get("domain_name_servers", {})
    if isinstance(servers, dict):
        return [value.get("value") for value in servers.values() if value.get("selected")]
    return [item.strip() for item in str(servers).split(",") if item.strip()]

def _set_dns(servers):
    result = _api("POST", "/api/kea/dhcpv4/set_subnet/" + SUBNET_UUID,
                  {"subnet4": {"option_data": {"domain_name_servers": ",".join(servers)}}})
    if result.get("result") != "saved":
        raise RuntimeError("Kea avviste DNS-oppdateringen: %s" % result)
    result = _api("POST", "/api/kea/service/reconfigure", {})
    if result.get("status") != "ok":
        raise RuntimeError("Kea kunne ikke reconfigureres: %s" % result)

def reconcile():
    checks = health()
    any_healthy = any(checks.values())
    state = _state()
    state["both_down"] = state.get("both_down", 0) + 1 if not any_healthy else 0
    state["healthy"] = state.get("healthy", 0) + 1 if any_healthy else 0
    before = configured_dns()
    mode = "unbound" if before == [UNBOUND] else "pihole"
    transition = error = None
    try:
        if mode == "pihole" and state["both_down"] >= FAIL_THRESHOLD:
            _set_dns([UNBOUND])
            mode, transition = "unbound", "failover"
        elif mode == "unbound" and state["healthy"] >= RECOVER_THRESHOLD:
            _set_dns(list(PIHOLES))
            mode, transition = "pihole", "recovery"
    except RuntimeError as exc:
        error = str(exc)
    state.update({"mode": mode, "last_checks": checks,
                  "updated_at": datetime.now(TZ).isoformat(timespec="seconds")})
    _save(state)
    return {"checks": checks, "mode": mode, "transition": transition,
            "both_down_count": state["both_down"], "healthy_count": state["healthy"],
            "configured_dns_before": before, "error": error}

def snapshot():
    checks = health()
    state = _state()
    return {"checks": checks, "configured_dns": configured_dns(),
            "mode": state.get("mode"), "both_down_count": state.get("both_down", 0),
            "healthy_count": state.get("healthy", 0)}

