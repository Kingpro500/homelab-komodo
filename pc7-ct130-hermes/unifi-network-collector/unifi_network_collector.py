#!/usr/bin/env python3
"""Read-only UniFi device and port health sampler for Hermes."""
import json
import os
import sqlite3
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from http.cookiejar import CookieJar

HOME = "/home/hermes"
ENV_FILE = os.environ.get("UNIFI_ENVFILE", HOME + "/.hermes/unifi.env")
DB = os.environ.get("WAN_FLAP_DB", HOME + "/.hermes/data/wan_flaps.db")


def envfile():
    values = {}
    with open(ENV_FILE) as handle:
        for line in handle:
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.rstrip("\n").split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api(values):
    base = values["UNIFI_URL"].rstrip("/")
    cookies = CookieJar()
    client = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookies),
        urllib.request.HTTPSHandler(context=ssl._create_unverified_context()),
    )
    def fetch(path, payload=None):
        request = urllib.request.Request(
            base + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json"},
        )
        with client.open(request, timeout=15) as response:
            return json.load(response)
    fetch("/api/login", {"username": values["UNIFI_USERNAME"], "password": values["UNIFI_PASSWORD"]})
    site = fetch("/api/self/sites")["data"][0]["name"]
    devices = fetch(f"/api/s/{site}/stat/device").get("data", [])
    clients = fetch("/api/s/default/stat/sta").get("data", [])
    return devices, clients


def main():
    observed = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    db = sqlite3.connect(DB)
    db.executescript("""
      CREATE TABLE IF NOT EXISTS unifi_device_snapshots (
        observed_at TEXT NOT NULL, name TEXT NOT NULL, device_type TEXT NOT NULL,
        state INTEGER, uplink TEXT, port_count INTEGER, sample_error TEXT,
        PRIMARY KEY (observed_at, name)
      );
      CREATE TABLE IF NOT EXISTS unifi_port_snapshots (
        observed_at TEXT NOT NULL, device_name TEXT NOT NULL, port_index INTEGER NOT NULL,
        port_name TEXT, up INTEGER, speed_mbps INTEGER, rx_errors INTEGER, tx_errors INTEGER,
        rx_dropped INTEGER, tx_dropped INTEGER, sample_error TEXT,
        PRIMARY KEY (observed_at, device_name, port_index)
      );
      CREATE INDEX IF NOT EXISTS unifi_device_snapshots_seen ON unifi_device_snapshots(observed_at);
      CREATE INDEX IF NOT EXISTS unifi_port_snapshots_seen ON unifi_port_snapshots(observed_at);
      CREATE TABLE IF NOT EXISTS unifi_client_snapshots (
        observed_at TEXT NOT NULL, mac TEXT NOT NULL, ip TEXT, name TEXT, hostname TEXT,
        radio TEXT, signal_dbm REAL, tx_retries INTEGER, tx_packets INTEGER,
        retry_ratio REAL, tx_rate_mbps REAL, satisfaction REAL, PRIMARY KEY (mac)
      );
      CREATE TABLE IF NOT EXISTS unifi_radio_snapshots (
        observed_at TEXT NOT NULL, ap TEXT NOT NULL, radio TEXT NOT NULL,
        channel_utilization REAL, PRIMARY KEY (ap, radio)
      );
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(unifi_port_snapshots)")}
    for column in ("rx_errors", "tx_errors", "rx_dropped", "tx_dropped"):
        if column not in columns:
            db.execute("ALTER TABLE unifi_port_snapshots ADD COLUMN %s INTEGER" % column)
    try:
        devices, clients = api(envfile())
        for device in devices:
            name = str(device.get("name") or device.get("hostname") or "unnamed")
            kind = str(device.get("type") or "unknown")
            state = device.get("state")
            uplink = device.get("uplink", {}).get("name") or device.get("uplink", {}).get("uplink_remote_port")
            db.execute("INSERT OR REPLACE INTO unifi_device_snapshots VALUES (?,?,?,?,?,?,NULL)",
                       (observed, name, kind, state, str(uplink or ""), len(device.get("port_table") or [])))
            if kind == "usw":
                for port in device.get("port_table") or []:
                    index = port.get("port_idx")
                    if index is None:
                        continue
                    db.execute("""INSERT OR REPLACE INTO unifi_port_snapshots
                                  (observed_at,device_name,port_index,port_name,up,speed_mbps,
                                   rx_errors,tx_errors,rx_dropped,tx_dropped,sample_error)
                                  VALUES (?,?,?,?,?,?,?,?,?,?,NULL)""",
                               (observed, name, int(index), str(port.get("name") or ""),
                                int(bool(port.get("up"))), int(port.get("speed") or 0),
                                int(port.get("rx_errors") or 0), int(port.get("tx_errors") or 0),
                                int(port.get("rx_dropped") or 0), int(port.get("tx_dropped") or 0)))
        for client in clients:
            if client.get("is_wired") is not False:
                continue
            mac = str(client.get("mac") or "").strip()
            if not mac:
                continue
            previous = db.execute("SELECT tx_retries,tx_packets FROM unifi_client_snapshots WHERE mac=?", (mac,)).fetchone()
            retries = client.get("tx_retries")
            packets = client.get("tx_packets")
            ratio = None
            if previous and retries is not None and packets is not None and previous[0] is not None and previous[1] is not None:
                dr, dp = int(retries) - int(previous[0]), int(packets) - int(previous[1])
                if dr >= 0 and dp > 0:
                    ratio = dr / dp
            db.execute("""INSERT OR REPLACE INTO unifi_client_snapshots
                (observed_at,mac,ip,name,hostname,radio,signal_dbm,tx_retries,tx_packets,
                 retry_ratio,tx_rate_mbps,satisfaction) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (observed, mac, client.get("ip"), client.get("name"), client.get("hostname"),
                 client.get("radio"), client.get("signal"), retries, packets, ratio,
                 (float(client["tx_rate"]) / 1000 if client.get("tx_rate") is not None else None),
                 client.get("satisfaction")))
        for device in devices:
            ap = str(device.get("name") or device.get("hostname") or "unnamed")
            for radio in device.get("radio_table_stats") or []:
                radio_name = str(radio.get("radio") or radio.get("radio_name") or "")
                if not radio_name or radio.get("cu_total") is None:
                    continue
                db.execute("""INSERT OR REPLACE INTO unifi_radio_snapshots
                    (observed_at,ap,radio,channel_utilization) VALUES (?,?,?,?)""",
                    (observed, ap, radio_name, radio.get("cu_total")))
    except Exception as exc:
        db.execute("INSERT OR REPLACE INTO unifi_device_snapshots VALUES (?,?,?,?,?,?,?)",
                   (observed, "collector", "collector", None, "", 0, str(exc)[:300]))
        db.commit()
        raise
    db.commit()


if __name__ == "__main__":
    main()
