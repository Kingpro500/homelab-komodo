#!/usr/bin/env python3
"""Generate and display the conservative parallel-work B report."""
import argparse
import json
import os
from datetime import datetime, timezone

BASE = os.path.expanduser("~/.hermes/parallel")
STATE = os.path.join(BASE, "state.json")
REPORT = os.path.join(BASE, "report.json")
SEED = [
    {"id": "K44", "class": "A", "status": "B", "ct": 340,
     "reason": "avvek fra godkjent sikkerhetsomfang", "auto": False},
    {"id": "K45", "class": "B", "status": "venter_pa_roger", "ct": 150,
     "reason": "manuell godkjenning kreves", "auto": False},
    {"id": "K47", "class": "A", "status": "avsluttet", "ct": 0,
     "reason": "historisk oppgave avsluttet", "auto": False},
]


def load_tasks():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh).get("tasks", SEED)
    return SEED


def generate():
    os.makedirs(BASE, exist_ok=True)
    tasks = load_tasks()
    report = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "b_tasks": [t for t in tasks if t.get("status") in ("B", "venter_pa_roger") or t.get("class") == "B"],
    }
    tmp = REPORT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, REPORT)
    return report


def show_b():
    if os.path.exists(REPORT):
        with open(REPORT, encoding="utf-8") as fh:
            report = json.load(fh)
    else:
        report = generate()
    for task in report.get("b_tasks", []):
        print(f"{task['id']}: {task.get('reason', '')}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--show-b", action="store_true")
    args = parser.parse_args()
    if args.generate:
        generate()
    if args.show_b:
        show_b()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
