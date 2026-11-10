#!/bin/bash
# CT baseline + emergency fix for Debian LXCs in the homelab.
# Safe to run repeatedly. Usage inside a CT (as root):
#   curl -fsSL https://raw.githubusercontent.com/Kingpro500/homelab-komodo/main/scripts/ct-fix.sh | bash
# DNS set here lasts until the next CT restart unless the CT's DNS in Proxmox is also
# set to: domain lan.local, servers 10.0.0.115 10.0.0.118.
export DEBIAN_FRONTEND=noninteractive
FAIL=0
ok(){ printf '  OK    %s\n' "$1"; }
bad(){ printf '  FEIL  %s\n' "$1"; FAIL=1; }
echo "== CT-fiks $(hostname) $(date '+%F %T')"

echo "-- 1. Nettverk"
ip -4 -br addr show scope global
GW=$(ip -4 route show default | awk '{print $3; exit}')
[ -n "$GW" ] && ok "default gateway $GW" || bad "ingen default gateway – sjekk Network i Proxmox"
ping -c2 -W2 10.0.0.1 >/dev/null 2>&1 && ok "OPNsense 10.0.0.1 svarer" || bad "når ikke 10.0.0.1"

echo "-- 2. DNS"
printf 'search lan.local\nnameserver 10.0.0.115\nnameserver 10.0.0.118\nnameserver 10.0.0.1\n' > /etc/resolv.conf
getent hosts komodo.lan.local >/dev/null && ok "lokal DNS (komodo.lan.local)" || bad "lokal DNS"
getent hosts deb.debian.org  >/dev/null && ok "ekstern DNS" || bad "ekstern DNS"

echo "-- 3. Disk"
apt-get clean
USE=$(df --output=pcent / | tail -1 | tr -dc 0-9)
[ "$USE" -lt 90 ] && ok "rotdisk ${USE}% brukt" || bad "rotdisk ${USE}% full – utvid disken eller rydd før oppdatering"

echo "-- 4. Reparer og oppdater pakker"
dpkg --configure -a
apt-get -f install -y
if apt-get update && apt-get -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold full-upgrade -y; then
  ok "pakker oppdatert"
else
  bad "apt feilet – se meldingen over"
fi
apt-get install -y curl jq ca-certificates dnsutils iputils-ping nano htop
apt-get autoremove -y

echo "-- 5. Tidssone"
ln -sf /usr/share/zoneinfo/Europe/Oslo /etc/localtime
echo Europe/Oslo > /etc/timezone
ok "tidssone Europe/Oslo, klokka er $(date '+%T')"

echo "-- 6. Kontroll"
curl -fsS -m10 -o /dev/null https://deb.debian.org && ok "HTTPS ut på internett" || bad "HTTPS ut feiler"
if command -v docker >/dev/null; then
  systemctl is-active --quiet docker && ok "Docker kjører" || bad "Docker kjører ikke"
  docker ps --format '        {{.Names}}: {{.Status}}'
fi
[ -f /var/run/reboot-required ] && echo "  MERK  omstart anbefalt – kjør 'pct reboot <id>' fra verten"
[ "$FAIL" = 0 ] && echo "== ALT OK" || echo "== NOE FEILET – lim inn utskriften til Claude"
