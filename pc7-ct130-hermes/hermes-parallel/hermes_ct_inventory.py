#!/usr/bin/env python3
"""Read-only parallel inventory of available LXC guests."""
import concurrent.futures
import json
import os
import subprocess
import sys

NODES = ("pc6", "pc7", "pc8", "pc9")
OUT = os.path.expanduser("~/.hermes/parallel/inventory.json")


def one(node):
    try:
        p = subprocess.run(["ssh", node, "pct list"], capture_output=True,
                           text=True, timeout=30)
        if p.returncode:
            return {"node": node, "error": p.stderr.strip()}
        rows = []
        for line in p.stdout.splitlines()[1:]:
            x = line.split()
            if len(x) >= 3 and x[0].isdigit():
                lock, name = (x[2], x[3]) if len(x) >= 4 else ("", x[2])
                rows.append({"vmid": int(x[0]), "status": x[1],
                             "lock": lock, "name": name, "node": node})
        return {"node": node, "guests": rows}
    except Exception as exc:
        return {"node": node, "error": str(exc)}


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(NODES)) as ex:
        out = list(ex.map(one, NODES))
    out = sorted(out, key=lambda item: item["node"])
    guests = sorted((g for item in out for g in item.get("guests", [])),
                    key=lambda guest: (guest["vmid"], guest["node"]))
    result = {"nodes": out, "guests": guests}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, sort_keys=True, indent=2)
        fh.write("\n")
    os.replace(tmp, OUT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if all("error" not in item for item in out) else 1


if __name__ == "__main__":
    sys.exit(main())
