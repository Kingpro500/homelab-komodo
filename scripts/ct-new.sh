#!/bin/bash
# Run on a Proxmox node. Bare navnet er nok – resten har standardverdier og kan endres i Proxmox etterpå:
#   ct-new uptime                  -> neste ledige ID, 1 kjerne, 1024 MB, 8 GB, første ledige IP i 10.0.0.204-254
#   ct-new immich 4096 32 2        -> navn + ram_mb disk_gb kjerner
#   ct-new 130 immich [ram] [disk] [kjerner] [ip]   (gammel form med fast ID fungerer fortsatt)
# Lager en standard Debian 13-LXC og kjører ct-komodo (Komodo + stack hvis den finnes i Git).
set -euo pipefail
[ $# -ge 1 ] || { echo "Bruk: ct-new <tjeneste> [ram_mb] [disk_gb] [kjerner]   eller   ct-new <ctid> <tjeneste> ..."; exit 1; }
if [[ "$1" =~ ^[0-9]+$ ]]; then ID="$1"; AUTOID=0; shift; else ID=$(pvesh get /cluster/nextid); AUTOID=1; fi
SVC=$(echo "${1:?tjeneste mangler}" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\n' '-')
RAM="${2:-1024}"; DISK="${3:-8}"; CORES="${4:-1}"; IP="${5:-}"
NODE=$(hostname -s | tr '[:upper:]' '[:lower:]')
ok(){ printf '  OK    %s\n' "$1"; }; die(){ printf '  FEIL  %s\n' "$1"; exit 1; }
echo "== Ny CT $ID på $NODE: ${NODE}-ct${ID}-${SVC}"

# Klyngelås rundt valg av ID/IP og pct create, så to samtidige ct-new ikke tar samme IP
LOCK=/etc/pve/priv/lock/ct-new
GOT=0
for i in $(seq 1 60); do mkdir "$LOCK" 2>/dev/null && { GOT=1; break; }
  [ -d "$LOCK" ] && [ $(( $(date +%s) - $(stat -c %Y "$LOCK" 2>/dev/null || date +%s) )) -gt 300 ] && rmdir "$LOCK" 2>/dev/null
  [ "$i" = 1 ] && echo "  ...   venter på en annen ct-new i klyngen"; sleep 3; done
[ "$GOT" = 1 ] || die "fikk ikke klyngelås $LOCK (en annen ct-new kjører?)"
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
if [ "$AUTOID" = 1 ]; then ID=$(pvesh get /cluster/nextid); fi
pvesh get /cluster/nextid --vmid "$ID" >/dev/null 2>&1 || die "CT/VM-ID $ID er allerede i bruk i klyngen"
used(){ grep -qsE "ip=$1/" /etc/pve/nodes/*/lxc/*.conf /etc/pve/nodes/*/qemu-server/*.conf || ping -c1 -W1 "$1" >/dev/null 2>&1; }
if [ -z "$IP" ]; then
  for n in $(seq 204 254); do used "10.0.0.$n" || { IP="10.0.0.$n"; break; }; done
  [ -n "$IP" ] || die "ingen ledig IP i 10.0.0.204-254"
else
  used "$IP" && die "$IP er allerede i bruk"
fi
ok "IP $IP (fast, utenfor DHCP-poolen .2-.99)"

STOR=$(pvesm status --content rootdir 2>/dev/null | awk 'NR>1 && $3=="active"{print $1}' | grep -m1 -E '^local-lvm$' || true)
[ -n "$STOR" ] || STOR=$(pvesm status --content rootdir | awk 'NR>1 && $3=="active" && $2!="nfs" && $2!="dir"{print $1; exit}')
[ -n "$STOR" ] || die "fant ingen lokal lagring for CT-disk"
ok "lagring $STOR (${DISK} GB)"

TPL=$(pveam list local 2>/dev/null | awk '/debian-13-standard/{print $1}' | sort -V | tail -1)
if [ -z "$TPL" ]; then
  pveam update >/dev/null 2>&1 || true
  NEW=$(pveam available --section system | awk '/debian-13-standard.*amd64/{print $2}' | sort -V | tail -1)
  [ -n "$NEW" ] || die "fant ikke Debian 13-template"
  pveam download local "$NEW" >/dev/null || die "nedlasting av $NEW feilet"
  TPL="local:vztmpl/$NEW"
fi
ok "template $TPL"

KEYS=/root/.ssh/authorized_keys
pct create "$ID" "$TPL" \
  --hostname "$SVC" --unprivileged 1 --features nesting=1,keyctl=1 \
  --cores "$CORES" --memory "$RAM" --swap 512 --rootfs "$STOR:$DISK" \
  --net0 "name=eth0,bridge=vmbr0,firewall=1,gw=10.0.0.1,ip=$IP/24" \
  --nameserver "10.0.0.115 10.0.0.118" --searchdomain lan.local \
  --onboot 1 --timezone Europe/Oslo --ssh-public-keys "$KEYS" \
  --description "${NODE}-ct${ID}-${SVC} · $IP · opprettet $(date +%F) med ct-new" >/dev/null \
  || die "pct create feilet"
rmdir "$LOCK" 2>/dev/null; trap - EXIT
ok "CT $ID opprettet (${CORES} kjerne(r), ${RAM} MB RAM, ${DISK} GB disk)"
pct start "$ID"; for i in $(seq 1 30); do pct exec "$ID" -- true 2>/dev/null && break; sleep 2; done
ok "CT $ID startet"
exec bash <(curl -fsSL "https://raw.githubusercontent.com/Kingpro500/homelab-komodo/${HOMELAB_REF:-main}/scripts/ct-komodo.sh") "$ID" "$SVC"
