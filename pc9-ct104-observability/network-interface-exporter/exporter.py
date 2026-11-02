#!/usr/bin/env python3
"""Minimal Prometheus exporter for Linux network-interface counters."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path


SYSFS_ROOT = Path(os.getenv("NETWORK_SYSFS_ROOT", "/sys/class/net"))
INTERFACES = tuple(
    item.strip()
    for item in os.getenv("NETWORK_INTERFACES", "eth0").split(",")
    if item.strip()
)
LISTEN_ADDRESS = os.getenv("LISTEN_ADDRESS", "0.0.0.0")
LISTEN_PORT = int(os.getenv("LISTEN_PORT", "9100"))

COUNTERS = {
    "rx_bytes": "Bytes received by the network interface",
    "tx_bytes": "Bytes transmitted by the network interface",
    "rx_packets": "Packets received by the network interface",
    "tx_packets": "Packets transmitted by the network interface",
    "rx_errors": "Receive errors reported by the network interface",
    "tx_errors": "Transmit errors reported by the network interface",
    "rx_dropped": "Received packets dropped by the network interface",
    "tx_dropped": "Transmitted packets dropped by the network interface",
}


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render_metrics() -> bytes:
    lines = [
        "# HELP network_interface_exporter_scrape_success Whether all configured interface counters were read",
        "# TYPE network_interface_exporter_scrape_success gauge",
    ]
    success = 1

    for counter, help_text in COUNTERS.items():
        metric = f"network_interface_{counter}_total"
        lines.extend((f"# HELP {metric} {help_text}", f"# TYPE {metric} counter"))
        for interface in INTERFACES:
            try:
                value = int((SYSFS_ROOT / interface / "statistics" / counter).read_text().strip())
            except (OSError, ValueError):
                success = 0
                continue
            lines.append(f'{metric}{{interface="{escape_label(interface)}"}} {value}')

    lines.append(f"network_interface_exporter_scrape_success {success}")
    return ("\n".join(lines) + "\n").encode()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/-/healthy":
            body = b"OK\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
        elif self.path == "/metrics":
            body = render_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        else:
            body = b"Not found\n"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer((LISTEN_ADDRESS, LISTEN_PORT), Handler).serve_forever()
