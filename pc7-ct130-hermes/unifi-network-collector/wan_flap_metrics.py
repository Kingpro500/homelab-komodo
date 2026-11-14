#!/usr/bin/env python3
"""Small Prometheus endpoint for the durable OPNsense WAN-flap history."""
import os
import sqlite3
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get("WAN_FLAP_DB", "/home/hermes/.hermes/data/wan_flaps.db")
PORT = int(os.environ.get("WAN_FLAP_METRICS_PORT", "9130"))


def metrics():
    now = datetime.now()
    since = (now - timedelta(hours=24)).isoformat()
    db = sqlite3.connect(DB)
    total, duration = db.execute("SELECT COUNT(*), COALESCE(SUM(duration_s),0) FROM outages").fetchone()
    day_count, day_duration = db.execute(
        "SELECT COUNT(*), COALESCE(SUM(duration_s),0) FROM outages WHERE ended_at >= ?", (since,)
    ).fetchone()
    last = db.execute("SELECT started_at,duration_s FROM outages ORDER BY ended_at DESC LIMIT 1").fetchone()
    gateway = db.execute("""
        SELECT ended_at,gateway_status,gateway_loss_pct,gateway_delay_ms
        FROM outages ORDER BY ended_at DESC LIMIT 1
    """).fetchone()
    interface = db.execute("""
        SELECT observed_at,received_packets,sent_packets,received_bytes,sent_bytes,
               received_errors,dropped_packets,send_errors,collisions
        FROM interface_snapshots ORDER BY observed_at DESC LIMIT 1
    """).fetchone()
    fast = db.execute("""
        SELECT observed_at,received_errors,dropped_packets,send_errors,collisions,
               gateway_status,gateway_loss_pct,gateway_delay_ms,sample_error
        FROM wan_fast_snapshots ORDER BY observed_at DESC LIMIT 1
    """).fetchone() if "wan_fast_snapshots" in {
        row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    } else None
    neighbor = db.execute("""
        SELECT observed_at,present,manufacturer,sample_error
        FROM wan_neighbor_snapshots ORDER BY observed_at DESC LIMIT 1
    """).fetchone() if "wan_neighbor_snapshots" in {
        row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    } else None
    status = db.execute("""
        SELECT observed_at,crash_reporter_active,sample_error
        FROM opnsense_status_snapshots ORDER BY observed_at DESC LIMIT 1
    """).fetchone() if "opnsense_status_snapshots" in {
        row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    } else None
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    client_rows = []
    radio_rows = []
    try:
        cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
        client_rows = db.execute("""SELECT mac,ip,name,hostname,radio,signal_dbm,retry_ratio,tx_rate_mbps,satisfaction
            FROM unifi_client_snapshots WHERE observed_at >= ?""", (cutoff,)).fetchall()
        radio_rows = db.execute("""SELECT ap,radio,channel_utilization FROM unifi_radio_snapshots
            WHERE observed_at >= ?""", (cutoff,)).fetchall()
    except Exception:
        client_rows, radio_rows = [], []
    unifi_observed = None
    unifi_error = None
    unifi_devices = []
    unifi_ports = []
    if "unifi_device_snapshots" in tables:
        unifi_observed = db.execute("SELECT MAX(observed_at) FROM unifi_device_snapshots").fetchone()[0]
        if unifi_observed:
            failure = db.execute(
                "SELECT sample_error FROM unifi_device_snapshots WHERE observed_at=? AND name='collector'",
                (unifi_observed,),
            ).fetchone()
            unifi_error = failure[0] if failure else None
            unifi_devices = db.execute("""
                SELECT name,device_type,state FROM unifi_device_snapshots
                WHERE observed_at=? AND sample_error IS NULL
            """, (unifi_observed,)).fetchall()
            if "unifi_port_snapshots" in tables:
                unifi_ports = db.execute("""
                    SELECT device_name,port_index,port_name,up,speed_mbps,
                           rx_errors,tx_errors,rx_dropped,tx_dropped
                    FROM unifi_port_snapshots
                    WHERE observed_at=?
                """, (unifi_observed,)).fetchall()
    probe_rows = db.execute("""
        SELECT p.target,p.state,p.observed_at,p.latency_ms,
               (SELECT COUNT(*) FROM probe_events f WHERE f.target=p.target AND f.state='down')
        FROM probe_events p
        JOIN (SELECT target, MAX(id) AS id FROM probe_events GROUP BY target) newest ON newest.id=p.id
        ORDER BY p.target
    """).fetchall()
    db.close()
    last_ts = 0
    last_duration = 0
    gateway_ts = 0
    gateway_status = "unknown"
    gateway_loss = 0
    gateway_delay = 0
    interface_ts = 0
    interface_counters = (0,) * 8
    fast_ts = 0
    fast_counters = (0,) * 4
    fast_status = "unknown"
    fast_loss = 0
    fast_delay = 0
    fast_up = 0
    neighbor_ts = 0
    neighbor_present = 0
    neighbor_sampler_up = 0
    neighbor_manufacturer = "unknown"
    status_ts, crash_active, status_sampler_up = 0, 0, 0
    unifi_ts = datetime.fromisoformat(unifi_observed).timestamp() if unifi_observed else 0
    unifi_up = int(bool(unifi_observed) and not unifi_error)
    if last:
        last_ts = datetime.fromisoformat(last[0]).timestamp()
        last_duration = last[1]
    if gateway:
        gateway_ts = datetime.fromisoformat(gateway[0]).timestamp()
        gateway_status = str(gateway[1] or "unknown")
        gateway_loss = gateway[2] or 0
        gateway_delay = gateway[3] or 0
    if interface:
        interface_ts = datetime.fromisoformat(interface[0]).timestamp()
        interface_counters = interface[1:]
    if fast:
        fast_ts = datetime.fromisoformat(fast[0]).timestamp()
        fast_counters = tuple(value or 0 for value in fast[1:5])
        fast_status = str(fast[5] or "unknown")
        fast_loss = fast[6] or 0
        fast_delay = fast[7] or 0
        fast_up = int(not fast[8])
    if neighbor:
        neighbor_ts = datetime.fromisoformat(neighbor[0]).timestamp()
        neighbor_present = int(bool(neighbor[1]))
        neighbor_manufacturer = str(neighbor[2] or "unknown")
        neighbor_sampler_up = int(not neighbor[3])
    if status:
        status_ts = datetime.fromisoformat(status[0]).timestamp()
        crash_active = int(bool(status[1]))
        status_sampler_up = int(not status[2])
    lines = [
        "# HELP opnsense_wan_flaps_total Total physical igc1 link outages retained in SQLite.",
        "# TYPE opnsense_wan_flaps_total counter",
        "opnsense_wan_flaps_total %s" % total,
        "# HELP opnsense_wan_flap_downtime_seconds_total Total physical WAN downtime retained in SQLite.",
        "# TYPE opnsense_wan_flap_downtime_seconds_total counter",
        "opnsense_wan_flap_downtime_seconds_total %s" % duration,
        "# HELP opnsense_wan_flaps_24h Physical WAN link outages in the last 24 hours.",
        "# TYPE opnsense_wan_flaps_24h gauge",
        "opnsense_wan_flaps_24h %s" % day_count,
        "# HELP opnsense_wan_flap_downtime_seconds_24h Physical WAN downtime in the last 24 hours.",
        "# TYPE opnsense_wan_flap_downtime_seconds_24h gauge",
        "opnsense_wan_flap_downtime_seconds_24h %s" % day_duration,
        "# HELP opnsense_wan_flap_last_timestamp_seconds Start time of the latest physical WAN outage.",
        "# TYPE opnsense_wan_flap_last_timestamp_seconds gauge",
        "opnsense_wan_flap_last_timestamp_seconds %s" % last_ts,
        "# HELP opnsense_wan_flap_last_duration_seconds Duration of the latest physical WAN outage.",
        "# TYPE opnsense_wan_flap_last_duration_seconds gauge",
        "opnsense_wan_flap_last_duration_seconds %s" % last_duration,
        "# HELP opnsense_wan_gateway_snapshot_timestamp_seconds Timestamp of the gateway snapshot captured with the latest physical flap.",
        "# TYPE opnsense_wan_gateway_snapshot_timestamp_seconds gauge",
        "opnsense_wan_gateway_snapshot_timestamp_seconds %s" % gateway_ts,
        "# HELP opnsense_wan_gateway_loss_percent Gateway packet loss at the latest physical flap.",
        "# TYPE opnsense_wan_gateway_loss_percent gauge",
        "opnsense_wan_gateway_loss_percent %s" % gateway_loss,
        "# HELP opnsense_wan_gateway_delay_milliseconds Gateway latency at the latest physical flap.",
        "# TYPE opnsense_wan_gateway_delay_milliseconds gauge",
        "opnsense_wan_gateway_delay_milliseconds %s" % gateway_delay,
        "# HELP opnsense_wan_gateway_status Latest gateway status captured with a physical flap.",
        "# TYPE opnsense_wan_gateway_status gauge",
        'opnsense_wan_gateway_status{status="%s"} 1' % gateway_status.replace('"', r'\\"'),
        "# HELP opnsense_wan_nic_snapshot_timestamp_seconds Timestamp of the latest igc1 hardware counter snapshot.",
        "# TYPE opnsense_wan_nic_snapshot_timestamp_seconds gauge",
        "opnsense_wan_nic_snapshot_timestamp_seconds %s" % interface_ts,
        "# HELP opnsense_wan_fast_snapshot_timestamp_seconds Timestamp of the five-second NIC and gateway sample.",
        "# TYPE opnsense_wan_fast_snapshot_timestamp_seconds gauge",
        "opnsense_wan_fast_snapshot_timestamp_seconds %s" % fast_ts,
        "# HELP opnsense_wan_fast_sampler_up Whether the latest five-second OPNsense API sample completed.",
        "# TYPE opnsense_wan_fast_sampler_up gauge",
        "opnsense_wan_fast_sampler_up %s" % fast_up,
        "# HELP opnsense_wan_fast_gateway_loss_percent Gateway packet loss from the latest five-second sample.",
        "# TYPE opnsense_wan_fast_gateway_loss_percent gauge",
        "opnsense_wan_fast_gateway_loss_percent %s" % fast_loss,
        "# HELP opnsense_wan_fast_gateway_delay_milliseconds Gateway latency from the latest five-second sample.",
        "# TYPE opnsense_wan_fast_gateway_delay_milliseconds gauge",
        "opnsense_wan_fast_gateway_delay_milliseconds %s" % fast_delay,
        "# HELP opnsense_wan_fast_gateway_status Latest gateway status from the five-second sample.",
        "# TYPE opnsense_wan_fast_gateway_status gauge",
        'opnsense_wan_fast_gateway_status{status="%s"} 1' % fast_status.replace('"', r'\\"'),
        "# HELP opnsense_wan_next_hop_snapshot_timestamp_seconds Timestamp of the latest WAN ARP-neighbor snapshot.",
        "# TYPE opnsense_wan_next_hop_snapshot_timestamp_seconds gauge",
        "opnsense_wan_next_hop_snapshot_timestamp_seconds %s" % neighbor_ts,
        "# HELP opnsense_wan_next_hop_present Whether OPNsense currently has a dynamic ARP neighbor on igc1.",
        "# TYPE opnsense_wan_next_hop_present gauge",
        "opnsense_wan_next_hop_present %s" % neighbor_present,
        "# HELP opnsense_wan_next_hop_sampler_up Whether the ARP-neighbor query completed.",
        "# TYPE opnsense_wan_next_hop_sampler_up gauge",
        "opnsense_wan_next_hop_sampler_up %s" % neighbor_sampler_up,
        "# HELP opnsense_wan_next_hop_info Registered manufacturer of the current dynamic WAN neighbor.",
        "# TYPE opnsense_wan_next_hop_info gauge",
        'opnsense_wan_next_hop_info{manufacturer="%s"} 1' % neighbor_manufacturer.replace('"', r'\\"'),
        "# HELP opnsense_crash_reporter_active Whether OPNsense reports a pending crash reporter event.",
        "# TYPE opnsense_crash_reporter_active gauge",
        "opnsense_crash_reporter_active %s" % crash_active,
        "# HELP opnsense_status_snapshot_timestamp_seconds Timestamp of the latest OPNsense system-status read.",
        "# TYPE opnsense_status_snapshot_timestamp_seconds gauge",
        "opnsense_status_snapshot_timestamp_seconds %s" % status_ts,
        "# HELP opnsense_status_sampler_up Whether the OPNsense system-status read succeeded.",
        "# TYPE opnsense_status_sampler_up gauge",
        "opnsense_status_sampler_up %s" % status_sampler_up,
        "# HELP unifi_network_collector_up Whether the latest read-only UniFi collection completed.",
        "# TYPE unifi_network_collector_up gauge",
        "unifi_network_collector_up %s" % unifi_up,
        "# HELP unifi_network_snapshot_timestamp_seconds Timestamp of the latest UniFi device/port sample.",
        "# TYPE unifi_network_snapshot_timestamp_seconds gauge",
        "unifi_network_snapshot_timestamp_seconds %s" % unifi_ts,
        "# HELP unifi_network_device_state Numeric UniFi controller state, retained verbatim for diagnosis.",
        "# TYPE unifi_network_device_state gauge",
        "# HELP unifi_network_switch_port_link_up Whether the observed UniFi switch port has carrier.",
        "# TYPE unifi_network_switch_port_link_up gauge",
        "# HELP unifi_network_switch_port_speed_mbps Observed UniFi switch port link speed.",
        "# TYPE unifi_network_switch_port_speed_mbps gauge",
        "# HELP unifi_network_switch_port_rx_errors_total Cumulative observed UniFi switch-port receive errors.",
        "# TYPE unifi_network_switch_port_rx_errors_total counter",
        "# HELP unifi_network_switch_port_tx_errors_total Cumulative observed UniFi switch-port transmit errors.",
        "# TYPE unifi_network_switch_port_tx_errors_total counter",
        "# HELP unifi_network_switch_port_rx_dropped_total Cumulative observed UniFi switch-port receive drops.",
        "# TYPE unifi_network_switch_port_rx_dropped_total counter",
        "# HELP unifi_network_switch_port_tx_dropped_total Cumulative observed UniFi switch-port transmit drops.",
        "# TYPE unifi_network_switch_port_tx_dropped_total counter",
        "# HELP opnsense_wan_probe_up Latest independent probe state (1 up, 0 down).",
        "# TYPE opnsense_wan_probe_up gauge",
        "# HELP opnsense_wan_probe_last_change_timestamp_seconds Timestamp of latest probe transition or down heartbeat.",
        "# TYPE opnsense_wan_probe_last_change_timestamp_seconds gauge",
        "# HELP opnsense_wan_probe_latency_milliseconds Latest ICMP latency when reachable.",
        "# TYPE opnsense_wan_probe_latency_milliseconds gauge",
        "# HELP opnsense_wan_probe_failures_total Stored down transitions/heartbeats by target.",
        "# TYPE opnsense_wan_probe_failures_total counter",
    ]
    nic_names = (
        "received_packets_total", "sent_packets_total", "received_bytes_total", "sent_bytes_total",
        "received_errors_total", "dropped_packets_total", "send_errors_total", "collisions_total",
    )
    for name, value in zip(nic_names, interface_counters):
        lines.extend((
            "# HELP opnsense_wan_nic_%s Cumulative igc1 hardware counter from OPNsense." % name,
            "# TYPE opnsense_wan_nic_%s counter" % name,
            "opnsense_wan_nic_%s %s" % (name, value),
        ))
    fast_nic_names = ("received_errors_total", "dropped_packets_total", "send_errors_total", "collisions_total")
    for name, value in zip(fast_nic_names, fast_counters):
        lines.extend((
            "# HELP opnsense_wan_fast_nic_%s Cumulative igc1 error counter sampled every five seconds." % name,
            "# TYPE opnsense_wan_fast_nic_%s counter" % name,
            "opnsense_wan_fast_nic_%s %s" % (name, value),
        ))
    for target, state, observed, latency, failures in probe_rows:
        labels = 'target="%s"' % target
        lines.append("opnsense_wan_probe_up{%s} %d" % (labels, state == "up"))
        lines.append("opnsense_wan_probe_last_change_timestamp_seconds{%s} %s" %
                     (labels, datetime.fromisoformat(observed).timestamp()))
        if latency is not None:
            lines.append("opnsense_wan_probe_latency_milliseconds{%s} %s" % (labels, latency))
        lines.append("opnsense_wan_probe_failures_total{%s} %s" % (labels, failures))
    def label(value):
        return str(value).replace('\\', r'\\\\').replace('"', r'\\"').replace('\n', r'\\n')
    for name, kind, state in unifi_devices:
        lines.append('unifi_network_device_state{name="%s",type="%s"} %s' %
                     (label(name), label(kind), state if state is not None else -1))
    for device, index, name, up, speed, rx_errors, tx_errors, rx_dropped, tx_dropped in unifi_ports:
        labels = 'device="%s",port_index="%s",port_name="%s"' % (label(device), index, label(name or ""))
        lines.append("unifi_network_switch_port_link_up{%s} %s" % (labels, int(bool(up))))
        lines.append("unifi_network_switch_port_speed_mbps{%s} %s" % (labels, speed or 0))
        lines.append("unifi_network_switch_port_rx_errors_total{%s} %s" % (labels, rx_errors or 0))
        lines.append("unifi_network_switch_port_tx_errors_total{%s} %s" % (labels, tx_errors or 0))
        lines.append("unifi_network_switch_port_rx_dropped_total{%s} %s" % (labels, rx_dropped or 0))
        lines.append("unifi_network_switch_port_tx_dropped_total{%s} %s" % (labels, tx_dropped or 0))
    for mac, ip, name, hostname, radio, signal, retry, tx_rate, satisfaction in client_rows:
        labels = 'mac="%s",ip="%s",name="%s",radio="%s"' % (label(mac), label(ip or ""), label(name or hostname or ""), label(radio or ""))
        for metric, value in (("unifi_client_signal_dbm", signal), ("unifi_client_retry_ratio", retry), ("unifi_client_tx_rate_mbps", tx_rate), ("unifi_client_satisfaction", satisfaction)):
            if value is not None:
                lines.append("%s{%s} %s" % (metric, labels, value))
    for ap, radio, utilization in radio_rows:
        if utilization is not None:
            lines.append('unifi_radio_channel_utilization{ap="%s",radio="%s"} %s' % (label(ap), label(radio), utilization))
    lines.append("")
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def do_GET(self):
        if self.path.split("?", 1)[0] != "/metrics":
            self.send_error(404)
            return
        body = metrics().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
