# blaff-logger — fanger nettverksblaff i sekundet de skjer

Laget etter blaffet i boden 10. nov 2026 20:56, da pc7 og pc8 mistet nettet samtidig og
«alt blinket». Målet er at neste blaff gir en rapport som viser **hva** som skjedde.

| Node | Hvorfor | Push |
| --- | --- | --- |
| pc6 (`nic3`) | utenfor boden — ser om boden forsvinner | ja (`ALERT=1`) |
| pc8 (USB-LAN) | inne i boden — ser det samme fra innsiden | nei (`ALERT=0`), bare logg |

**Hvert sekund:** ping til OPNsense, EdgeSwitch (.190), ERX (.191), Flex 2.5G (.192), AP (.193),
pc6, pc7, pc8, pc9 og 1.1.1.1, pluss pakkerate, kringkasting/multicast (talt direkte fra kortet —
USB-driveren teller ikke multicast), feil, drops og link. De siste 30 s holdes i minnet.

**Blaff** = minst 2 mål borte i 2 s, OPNsense/internett borte i 2 s, linkendring, eller
kringkasting > 8× normalt (min. 3000 pps) / pakkerate > 10× normalt (min. 50 000 pps).
Da startes et 20 s opptak av kringkasting/multicast/ARP, og når blaffet er over (10 s uten utløser)
+ 30 s etter, skrives rapporten.

**Rapport:** `/var/log/blaff/<host>-<tid>.json` (varighet, utløser, mål borte i sekunder, linkbrudd,
topprater, de 5 MAC-adressene som sendte mest kringkasting, alle målinger 30 s før/under/etter) +
`.pcap`. Beholdes i 30 dager. Sammendrag til n8n `/webhook/events` (FerretDB-hendelseslogg,
`type: nettverksblaff`); pc6 sender også push via `/webhook/homelab-alerts`, aldri 23–06.
Er n8n nede (den står i boden), køes rapporten i `/var/lib/blaff/spool` og sendes senere.

**Lese en rapport:** `python3 -m json.tool /var/log/blaff/<fil>.json | less`. Ved en sløyfe/storm er
`kringkasting.topp_avsender_mac` det viktigste feltet — slå opp MAC-en i UniFi/EdgeSwitch/OPNsense ARP.

Test: `EXTRA_TARGETS='{"test-a":"10.0.0.251","test-b":"10.0.0.252"}' PRE=3 POST=2 END_CLEAR=2 MAX_EVENT=4 N8N_EVENTS=http://127.0.0.1:9/x timeout 45 blaff-logger`
