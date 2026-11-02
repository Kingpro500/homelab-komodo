#!/usr/bin/env python3
"""Read-only Prometheus exporter for Linux interface counters and link state."""
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

INTERFACES = [x.strip() for x in os.environ.get("NETWORK_EXPORTER_INTERFACES", "eth0").split(",") if x.strip()]
PORT = int(os.environ.get("NETWORK_EXPORTER_PORT", "9122"))


def read_metrics():
    lines = [
        "# HELP network_interface_info Interface metadata.",
        "# TYPE network_interface_info gauge",
        "# HELP network_interface_link_up Whether the interface carrier is up.",
        "# TYPE network_interface_link_up gauge",
        "# HELP network_interface_rx_packets_total Received packets.",
        "# TYPE network_interface_rx_packets_total counter",
        "# HELP network_interface_rx_bytes_total Received bytes.",
        "# TYPE network_interface_rx_bytes_total counter",
        "# HELP network_interface_rx_errors_total Received packets with errors.",
        "# TYPE network_interface_rx_errors_total counter",
        "# HELP network_interface_rx_dropped_total Received packets dropped.",
        "# TYPE network_interface_rx_dropped_total counter",
        "# HELP network_interface_tx_packets_total Transmitted packets.",
        "# TYPE network_interface_tx_packets_total counter",
        "# HELP network_interface_tx_dropped_total Transmitted packets dropped.",
        "# TYPE network_interface_tx_dropped_total counter",
    ]
    now = int(time.time())
    for iface in INTERFACES:
        base = f"/sys/class/net/{iface}"
        if not os.path.isdir(base):
            continue

        def read(name):
            try:
                with open(f"{base}/statistics/{name}") as fh:
                    return int(fh.read().strip())
            except (OSError, ValueError):
                return 0

        try:
            with open(f"{base}/carrier") as fh:
                carrier = int(fh.read().strip())
        except (OSError, ValueError):
            carrier = 0

        label = f'interface="{iface}"'
        lines.extend([
            f"network_interface_info{{{label}}} 1",
            f"network_interface_link_up{{{label}}} {carrier}",
            f"network_interface_rx_packets_total{{{label}}} {read('rx_packets')}",
            f"network_interface_rx_bytes_total{{{label}}} {read('rx_bytes')}",
            f"network_interface_rx_errors_total{{{label}}} {read('rx_errors')}",
            f"network_interface_rx_dropped_total{{{label}}} {read('rx_dropped')}",
            f"network_interface_tx_packets_total{{{label}}} {read('tx_packets')}",
            f"network_interface_tx_dropped_total{{{label}}} {read('tx_dropped')}",
            f"network_interface_sample_timestamp_seconds{{{label}}} {now}",
        ])
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return
        body = read_metrics().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
