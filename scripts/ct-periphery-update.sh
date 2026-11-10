#!/bin/bash
# Oppdaterer systemd-Periphery i alle kjørende CT-er til samme versjon som Komodo Core.
# Kjør på en Proxmox-node:
#   ct-periphery-update            # denne noden, versjon = Core sin versjon
#   ct-periphery-update --alle     # alle noder i klyngen
#   ct-periphery-update --sjekk    # bare vis versjoner, endre ingenting (kan kombineres med --alle)
#   ct-periphery-update v2.3.4     # bestemt versjon (normalt: oppgrader Core først)
# Rekkefølge ved ny Komodo-versjon: 1) oppgrader Core (CT110), 2) kjør ct-periphery-update --alle.
# CT110 har Periphery i Core sin compose og oppdateres sammen med Core.
set -uo pipefail
CORE=http://10.0.0.117:9120
ALLE=0; SJEKK=0; VER=""
for a in "$@"; do case "$a" in --alle) ALLE=1;; --sjekk) SJEKK=1;; v*) VER="$a";; *) echo "Ukjent valg: $a"; exit 1;; esac; done
if [ -z "$VER" ]; then V=$(curl -fsS -m10 "$CORE/version" | tr -d '[:space:]'); [ -n "$V" ] || { echo "FEIL: fikk ikke Core-versjon fra $CORE/version"; exit 1; }; VER="v${V#v}"; fi
FLAGS=""; [ "$SJEKK" = 1 ] && FLAGS="--sjekk"

if [ "$ALLE" = 1 ]; then
  ME=$(hostname -s)
  awk '/^ *name:/{n=$2} /ring0_addr:/{print n, $2}' /etc/pve/corosync.conf | while read -r NAME IP; do
    if [ "$NAME" = "$ME" ]; then ct-periphery-update "$VER" $FLAGS </dev/null
    else timeout 600 ssh -n -o BatchMode=yes -o ConnectTimeout=6 "root@$IP" "ct-periphery-update $VER $FLAGS" || echo "== $NAME: FEIL – fikk ikke kjørt (ssh/node nede?)"; fi
  done
  exit 0
fi

N=$(hostname -s); OK=0; UPD=0; FAIL=0
echo "== $N: mål $VER$([ "$SJEKK" = 1 ] && echo ' (bare sjekk)')"
for C in $(pct list | awk 'NR>1 && $2=="running"{print $1}'); do
  X(){ pct exec "$C" -- env LANG=C.UTF-8 LC_ALL=C.UTF-8 sh -c "$1"; }
  X "test -x /usr/local/bin/periphery && systemctl list-unit-files periphery.service >/dev/null 2>&1" 2>/dev/null || continue
  CUR="v$(X '/usr/local/bin/periphery --version 2>/dev/null' | awk '{print $2}')"
  NAME=$(X "sed -n 's/^connect_as = \"\(.*\)\"/\1/p' /etc/komodo/periphery.config.toml" 2>/dev/null)
  if [ "$CUR" = "$VER" ]; then printf '  OK    CT%s %s er %s\n' "$C" "$NAME" "$CUR"; OK=$((OK+1)); continue; fi
  if [ "$(printf '%s\n%s\n' "$CUR" "$VER" | sort -V | tail -1)" = "$CUR" ]; then printf '  MERK  CT%s %s er %s, nyere enn mål %s – endres ikke\n' "$C" "$NAME" "$CUR" "$VER"; OK=$((OK+1)); continue; fi
  if [ "$SJEKK" = 1 ]; then printf '  NY    CT%s %s: %s -> %s\n' "$C" "$NAME" "$CUR" "$VER"; continue; fi
  T0=$(date '+%Y-%m-%d %H:%M:%S')
  if X "curl -fsSL https://raw.githubusercontent.com/moghtech/komodo/$VER/scripts/setup-periphery.py -o /root/setup-periphery.py && python3 /root/setup-periphery.py --version $VER >/var/log/periphery-update.log 2>&1 && systemctl daemon-reload && systemctl restart periphery"; then
    L=""; for i in $(seq 1 30); do L=$(X "journalctl -u periphery --no-pager --since '$T0' | grep -E 'Logged in to Komodo Core|Failed to login' | tail -1"); [ -n "$L" ] && break; sleep 2; done
    NEWV="v$(X '/usr/local/bin/periphery --version 2>/dev/null' | awk '{print $2}')"
    case "$L" in *"Logged in"*) printf '  OK    CT%s %s: %s -> %s, innlogget\n' "$C" "$NAME" "$CUR" "$NEWV"; UPD=$((UPD+1));;
      *) printf '  FEIL  CT%s %s: %s -> %s, ingen innlogging (%s)\n' "$C" "$NAME" "$CUR" "$NEWV" "${L:-ingen logg}"; FAIL=$((FAIL+1));; esac
  else printf '  FEIL  CT%s %s: oppdatering feilet (se /var/log/periphery-update.log i CT-en)\n' "$C" "$NAME"; FAIL=$((FAIL+1)); fi
done
echo "== $N: $OK allerede riktig, $UPD oppdatert, $FAIL feil"
