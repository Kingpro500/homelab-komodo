#!/usr/bin/env python3
"""Generate the daily autonomous CT-work report from local state."""
import argparse
import json
import os
from datetime import datetime, timezone

BASE = os.path.expanduser("~/.hermes/parallel")
STATE = os.path.join(BASE, "state.json")
INVENTORY = os.path.join(BASE, "inventory.json")
REPORT = os.path.join(BASE, "report.json")
SEED = [
    {"id": "K44", "class": "A", "status": "B", "ct": 340,
     "reason": "avvek fra godkjent sikkerhetsomfang", "auto": False},
    {"id": "K45", "class": "B", "status": "venter_pa_roger", "ct": 150,
     "reason": "manuell godkjenning kreves", "auto": False},
    {"id": "K47", "class": "A", "status": "avsluttet", "ct": 0,
     "reason": "historisk oppgave avsluttet", "auto": False},
]


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def generate():
    os.makedirs(BASE, exist_ok=True)
    state = read_json(STATE, {"tasks": SEED, "paused": False,
                              "consecutive_a_failures": 0})
    inventory = read_json(INVENTORY, {"nodes": [], "guests": [],
                                      "error": "inventory not run yet"})
    tasks = state.get("tasks", SEED)
    b_tasks = [t for t in tasks if t.get("status") in ("B", "venter_pa_roger")
               or t.get("class") == "B"]
    report = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inventory": inventory,
        "a_tasks": [t for t in tasks if t.get("class") == "A"],
        "a_failures": state.get("a_failures", []),
        "consecutive_a_failures": state.get("consecutive_a_failures", 0),
        "paused": bool(state.get("paused", False)),
        "active_locks": state.get("active_locks", []),
        "b_list": [{"number": i, **task} for i, task in enumerate(b_tasks, 1)],
    }
    tmp = REPORT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, REPORT)
    return report


def show_b():
    report = read_json(REPORT, generate())
    for task in report.get("b_list", []):
        print(f"{task['number']}. {task['id']}: {task.get('reason', '')}")


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
