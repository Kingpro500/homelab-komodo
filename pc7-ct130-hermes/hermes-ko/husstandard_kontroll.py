#!/usr/bin/env python3
"""Kontrollkommando for husstandard-oppgaver i hermes-ko.

    husstandard_kontroll.py <vmid> [--ma-kjore] [--godta-navn]

Exit 0 bare når ct-ops verify ikke har andre avvik enn dem som er godtatt.
--ma-kjore   CT-en kjørte da oppgaven ble laget: den må fortsatt kjøre og Komodo-serveren
             være Ok. (verify på en stoppet CT måler ikke avvikene og gir falsk ok.)
--godta-navn Navneavvik (Komodo-server-, stack-, run_directory- og Proxmox-navn) godtas;
             de er utenfor oppgaven til Roger har bestemt.
"""
import json, re, sys, urllib.request

NAVN = r"^(Komodo-server heter|Proxmox-navn|stack «[^»]+» burde hete|stack «[^»]+»: run_directory)"

def main(a):
    vmid = int(a[0]); ma_kjore = "--ma-kjore" in a; godta_navn = "--godta-navn" in a
    req = urllib.request.Request("http://10.0.0.119:5678/webhook/ct-ops",
                                 json.dumps({"action": "verify", "vmid": vmid}).encode(),
                                 {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=170))
    r = d.get("resultat") or {}
    inv = r.get("inventory") or {}
    dev = r.get("deviations") or []
    navn = [x for x in dev if godta_navn and re.match(NAVN, x)]
    rest = [x for x in dev if x not in navn]
    if ma_kjore:
        if inv.get("status") != "running":
            rest.append("CT%d kjører ikke (status %s), men kjørte før oppgaven" % (vmid, inv.get("status")))
        if (inv.get("server") or {}).get("state") != "Ok":
            rest.append("Komodo-serveren er ikke Ok (%s)" % (inv.get("server") or {}).get("state"))
    print(d.get("status"), d.get("kvalitetssjekk"))
    print("CT-status:", inv.get("status"), "| Komodo-server:", (inv.get("server") or {}).get("state"),
          "| Periphery:", (inv.get("periphery") or {}).get("kind"), "| OS:", (inv.get("periphery") or {}).get("os"),
          "| Docker:", (inv.get("periphery") or {}).get("docker_source"))
    if navn: print("Navneavvik, utenfor oppgaven og godtatt:", json.dumps(navn, ensure_ascii=False))
    print("Avvik som må rettes:", json.dumps(rest, ensure_ascii=False))
    return 0 if r.get("vmid") == vmid and not rest else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
