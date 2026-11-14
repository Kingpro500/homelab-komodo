#!/usr/bin/env python3
"""Oppdater ukesrapporten på linjekvalitet-siden uten AI-kall."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import re
import shlex
import subprocess
import sys
import urllib.request

DATA_URL = "http://10.0.0.124:3020/linjekvalitet.json"
DRIFT_URL = "http://10.0.0.135:9118/drift"
REMOTE = "/opt/moved-services/nettkart-repo/docs/network-map/linjekvalitet.html"
NOTIFY = "/home/hermes/.hermes/scripts/notify_ha.py"


def fetch(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError(f"Kilde feilet: {url}: {exc}") from exc


def nonnull(rows, key):
    return [r[key] for r in rows if r.get(key) is not None]


def median(rows, key):
    values = nonnull(rows, key)
    if not values:
        return None
    values = sorted(values)
    n = len(values)
    return (values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2)


def fmt(value):
    if value is None:
        return "ingen data"
    return f"{value:.1f}".replace(".", ",")


def integer_total(rows, key):
    return sum(r.get(key) or 0 for r in rows)


def report_rows(data):
    today = dt.date.today()
    end = today - dt.timedelta(days=1)
    start = end - dt.timedelta(days=6)
    prev_end = start - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=6)
    by_date = {dt.date.fromisoformat(r["dato"]): r for r in data.get("dager", [])}
    week = [by_date.get(start + dt.timedelta(days=i), {"dato": (start + dt.timedelta(days=i)).isoformat()}) for i in range(7)]
    previous = [by_date.get(prev_start + dt.timedelta(days=i), {"dato": (prev_start + dt.timedelta(days=i)).isoformat()}) for i in range(7)]
    return week, previous, end


def change(rows, old, key, unit):
    a, b = median(old, key), median(rows, key)
    if a is None or b is None:
        return f"{key} ingen data → ingen data"
    return f"{unit} {fmt(a)} → {fmt(b)} {unit_suffix(unit)} ({'+' if b-a >= 0 else ''}{fmt(b-a)})"


def unit_suffix(unit):
    return {"bufferbloat": "ms", "nedlasting": "Mbit/s", "opplasting": "Mbit/s"}.get(unit, unit)


def make_recommendations(rows):
    out = []
    n = sum((r.get("wan_brudd") or 0) >= 1 for r in rows)
    if n >= 3:
        out.append(f"Undersøk WAN-kabel og port: brudd {n} av 7 dager, {integer_total(rows, 'wan_brudd')} brudd, {integer_total(rows, 'wan_nedetid_s')} sekunder nede.")
    vals = nonnull(rows, "pakketap_prosent")
    n = sum(v > 1.0 for v in vals)
    if n >= 3:
        out.append(f"Pakketap over 1 prosent {n} av 7 dager (høyest {fmt(max(vals))}).")
    vals = nonnull(rows, "bufferbloat_ms")
    n = sum(v >= 30 for v in vals)
    if n >= 3:
        out.append(f"Bufferbloat over 30 ms {n} av 7 dager (høyest {fmt(max(vals))}): se over shaperen.")
    vals = nonnull(rows, "ned_median")
    n = sum(v < 500 for v in vals)
    if n >= 3:
        out.append(f"Nedlasting under 500 Mbit/s {n} av 7 dager (lavest {fmt(min(vals))}).")
    vals = nonnull(rows, "opp_median")
    n = sum(v < 500 for v in vals)
    if n >= 3:
        out.append(f"Opplasting under 500 Mbit/s {n} av 7 dager (lavest {fmt(min(vals))}).")
    vals = nonnull(rows, "fartstester_feilet")
    n = sum(v >= 2 for v in vals)
    if n >= 3:
        out.append(f"Fartstester feilet {n} av 7 dager ({sum(vals)} totalt).")
    return out[:3] or ["Ingen tiltak anbefales denne uken."]


def grade_median(rows):
    order = ["A+", "A", "B", "C", "D", "F"]
    chars = sorted((r.get("karakter") for r in rows if r.get("karakter")), key=order.index)
    if not chars:
        return "ingen data"
    return chars[(len(chars) - 1) // 2]


def build_ul(week, previous, drift, end):
    chars = [r.get("karakter") for r in week if r.get("karakter")]
    order = ["A+", "A", "B", "C", "D", "F"]
    worst = max(chars, key=lambda x: order.index(x)) if chars else "ingen data"
    middle = grade_median(week)
    bb, down, up = median(week, "bufferbloat_ms"), median(week, "ned_median"), median(week, "opp_median")
    bbs = nonnull(week, "bufferbloat_ms")
    dn, un = nonnull(week, "ned_min"), nonnull(week, "opp_min")
    issues = drift.get("issues", [])
    drift_text = "ingen funn" if not issues else "; ".join(f"{i.get('title', '')}" for i in issues)
    li = [
        f"Linjen: median karakter {middle}, dårligste karakter {worst}, median bufferbloat {fmt(bb)} ms, høyeste bufferbloat {fmt(max(bbs) if bbs else None)} ms, median nedlasting {fmt(down)} Mbit/s og laveste nedlasting {fmt(min(dn) if dn else None)} Mbit/s, median opplasting {fmt(up)} Mbit/s og laveste opplasting {fmt(min(un) if un else None)} Mbit/s, {integer_total(week, 'wan_brudd')} WAN-brudd, {integer_total(week, 'wan_nedetid_s')} sekunder WAN-nedetid, {integer_total(week, 'fartstester_feilet')} feilede fartstester.",
        "Endring mot forrige uke: " + ", ".join([change(week, previous, "bufferbloat_ms", "bufferbloat"), change(week, previous, "ned_median", "nedlasting"), change(week, previous, "opp_median", "opplasting"), f"WAN-brudd {integer_total(previous, 'wan_brudd')} → {integer_total(week, 'wan_brudd')} ({'+' if integer_total(week, 'wan_brudd')-integer_total(previous, 'wan_brudd') >= 0 else ''}{integer_total(week, 'wan_brudd')-integer_total(previous, 'wan_brudd')})", f"nedetid {integer_total(previous, 'wan_nedetid_s')} → {integer_total(week, 'wan_nedetid_s')} sekunder ({'+' if integer_total(week, 'wan_nedetid_s')-integer_total(previous, 'wan_nedetid_s') >= 0 else ''}{integer_total(week, 'wan_nedetid_s')-integer_total(previous, 'wan_nedetid_s')})"])+".",
        f"Drift: {drift.get('level', 'ukjent')}: {drift_text}.",
    ]
    li.extend(f"Anbefaling: {x}" for x in make_recommendations(week))
    safe = [html.escape(x, quote=False) for x in li]
    week_id = end.isocalendar().year, end.isocalendar().week
    return f'<ul id="funn" data-rapport="{week_id[0]:04d}-W{week_id[1]:02d}">\n' + "\n".join(f"<li>{x}</li>" for x in safe) + "\n</ul>"


def remote_read():
    r = subprocess.run(["ssh", "pc6", "pct", "exec", "120", "--", "cat", REMOTE], capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "lesing fra CT120 feilet")
    return r.stdout


def remote_write(text):
    payload = base64.b64encode(text.encode()).decode()
    r = subprocess.run(
        ["ssh", "pc6", "pct", "exec", "120", "--", "python3", "-c", shlex.quote(f"import sys,base64; open({REMOTE!r}, 'wb').write(base64.b64decode(sys.stdin.buffer.read()))")],
        input=payload,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "skriving til CT120 feilet")


def update_html(source, ul):
    matches = list(re.finditer(r'<ul\b[^>]*\bid=["\']funn["\'][^>]*>.*?</ul>', source, re.S | re.I))
    if len(matches) != 1:
        raise RuntimeError(f"fant {len(matches)} ul id=funn, forventet nøyaktig én")
    updated = source[:matches[0].start()] + ul + source[matches[0].end():]
    today = dt.date.today()
    months = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
    stamp = f"{today.day}. {months[today.month - 1]} {today.year}"
    pattern = r'(?m)^\s*<p class="sub">[^\n]*Sist gjennomgått[^\n]*</p>[^\n]*$'
    replacement = f'<p class="sub">Oppdateres av Hermes ved ukesrapport. Sist gjennomgått {stamp} (Hermes, ukesrapport).</p>'
    updated, count = re.subn(pattern, replacement, updated, count=1)
    if count != 1:
        raise RuntimeError("fant ikke nøyaktig én Sist gjennomgått-linje")
    return updated


def selftest():
    base = [{"wan_brudd": 1, "pakketap_prosent": 0, "bufferbloat_ms": 1, "ned_median": 600, "opp_median": 600, "fartstester_feilet": 2} for _ in range(2)] + [{"wan_brudd": 0, "pakketap_prosent": 0, "bufferbloat_ms": 1, "ned_median": 600, "opp_median": 600, "fartstester_feilet": 0} for _ in range(5)]
    assert not any("WAN-kabel" in x for x in make_recommendations(base))
    base[2]["wan_brudd"] = 1
    assert any("WAN-kabel" in x for x in make_recommendations(base))
    assert grade_median([{"karakter": x} for x in ["A+", "A+", "A+", "A+", "A", "A+", "A+"]]) == "A+"
    source = '<p class="sub">Oppdateres av agentene ved ukesrapport. Sist gjennomgått 14. nov 2026 (Claude).</p> (Hermes, ukesrapport)\n<ul id="funn" data-rapport="2026-W46"></ul>'
    updated = update_html(source, '<ul id="funn" data-rapport="2026-W46"></ul>')
    assert re.search(r'<p class="sub">Oppdateres av Hermes ved ukesrapport\. Sist gjennomgått \d{1,2}\. [a-z]{3} \d{4} \(Hermes, ukesrapport\)\.</p>$', updated.split("\n")[0])
    assert "</p> (Hermes" not in updated
    print("selvtest ok")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selvtest", action="store_true")
    args = parser.parse_args()
    if args.selvtest:
        selftest(); return 0
    data, drift = fetch(DATA_URL), fetch(DRIFT_URL)
    week, previous, end = report_rows(data)
    ul = build_ul(week, previous, drift, end)
    source = remote_read()
    updated = update_html(source, ul)
    if updated == source:
        return 0
    remote_write(updated)
    week_no = end.isocalendar().week
    r = subprocess.run(["ssh", "pc6", "pct", "exec", "120", "--", "/usr/local/sbin/nettkart-publish", f"Ukesrapport uke {week_no}", "--av", "hermes", "--berort", "CT120"], capture_output=True, text=True, timeout=300)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "nettkart-publish feilet")
    n = subprocess.run([sys.executable, NOTIFY, "Ukesrapport linjekvalitet", "Ukesrapporten er klar"], capture_output=True, text=True)
    if n.returncode:
        print(f"Melding feilet: {n.stderr.strip()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
