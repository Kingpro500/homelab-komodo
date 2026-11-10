#!/bin/bash
# Run on a Proxmox node:  ct-new <ctid> <tjeneste> [ram_mb] [disk_gb] [cores] [ip]
#   ct-new 127 uptime              -> 1024 MB, 8 GB, 1 core, first free IP in 10.0.0.204-254
#   ct-new 128 immich 4096 32 2    -> bigger CT
# Creates a standard Debian 13 LXC and then runs ct-komodo (Komodo + stack if it exists in Git).
set -euo pipefail
ID="${1:?Bruk: ct-new <ctid> <tjeneste> [ram_mb] [disk_gb] [cores] [ip]}"
SVC=$(echo "${2:?tjeneste mangler}" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\n' '-')
RAM="${3:-1024}"; DISK="${4:-8}"; CORES="${5:-1}"; IP="${6:-}"
NODE=$(hostname -s | tr '[:upper:]' '[:lower:]')
ok(){ printf '  OK    %s\n' "$1"; }; die(){ printf '  FEIL  %s\n' "$1"; exit 1; }
echo "== Ny CT $ID på $NODE: ${NODE}-ct${ID}-${SVC}"

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
ok "CT $ID opprettet (${CORES} kjerne(r), ${RAM} MB RAM, ${DISK} GB disk)"
pct start "$ID"; for i in $(seq 1 30); do pct exec "$ID" -- true 2>/dev/null && break; sleep 2; done
ok "CT $ID startet"
exec bash <(curl -fsSL https://raw.githubusercontent.com/Kingpro500/homelab-komodo/main/scripts/ct-komodo.sh) "$ID" "$SVC"
