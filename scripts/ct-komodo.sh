#!/bin/bash
# Run on a Proxmox node:  ct-komodo.sh <ctid> [tjeneste]
#   curl -fsSL https://raw.githubusercontent.com/Kingpro500/homelab-komodo/main/scripts/ct-komodo.sh | bash -s -- 126 netalertx
# Names the Komodo server <node>-ct<id>-<tjeneste>, sets CT DNS in Proxmox, makes sure
# nesting+keyctl are on, runs ct-fix.sh in the CT, then komodo-bootstrap.sh.
# Onboarding key is read from /root/.config/komodo/onboarding.key on the node (mode 600).
set -euo pipefail
RAW=https://raw.githubusercontent.com/Kingpro500/homelab-komodo/main/scripts
ID="${1:?Bruk: ct-komodo.sh <ctid> [tjeneste]}"
KEY=/root/.config/komodo/onboarding.key
pct status "$ID" >/dev/null 2>&1 || { echo "FEIL: CT $ID finnes ikke på $(hostname -s)"; exit 1; }
NODE=$(hostname -s | tr '[:upper:]' '[:lower:]')
SVC=$(echo "${2:-$(pct config "$ID" | awk '/^hostname:/{print $2}')}" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9-\n' '-')
NAME="${NODE}-ct${ID}-${SVC}"
[ -s "$KEY" ] || { echo "FEIL: mangler $KEY på $(hostname -s)"; exit 1; }
echo "== $NAME"

# Proxmox-oppsett: DNS, vertsnavn og features (nesting/keyctl kreves for Docker i unprivileged CT)
pct set "$ID" --nameserver "10.0.0.115 10.0.0.118" --searchdomain lan.local
CURHOST=$(pct config "$ID" | awk '/^hostname:/{print $2}')
[ "$CURHOST" = "$SVC" ] || { pct set "$ID" --hostname "$SVC"; echo "  OK    vertsnavn $CURHOST -> $SVC"; }
FEAT=$(pct config "$ID" | awk '/^features:/{print $2}')
NEED_REBOOT=0
case ",$FEAT," in *,nesting=1,*) ;; *) NEED_REBOOT=1;; esac
case ",$FEAT," in *,keyctl=1,*) ;; *) NEED_REBOOT=1;; esac
if [ "$NEED_REBOOT" = 1 ]; then pct set "$ID" --features nesting=1,keyctl=1; echo "  OK    features nesting=1,keyctl=1 satt"; fi
pct set "$ID" --onboot 1
if [ "$(pct status "$ID" | awk '{print $2}')" != running ]; then pct start "$ID"
elif [ "$NEED_REBOOT" = 1 ] || [ "$CURHOST" != "$SVC" ]; then pct reboot "$ID"; fi
for i in $(seq 1 30); do pct exec "$ID" -- true 2>/dev/null && break; sleep 2; done
echo "  OK    Proxmox: DNS lan.local, onboot=1, CT kjører"

# 1) grunnoppsett i CT-en
pct exec "$ID" -- bash -c "printf 'search lan.local\nnameserver 10.0.0.115\nnameserver 10.0.0.118\nnameserver 10.0.0.1\n' >/etc/resolv.conf; command -v curl >/dev/null || { apt-get -qq update && apt-get -qq install -y curl; } >/dev/null; curl -fsSL $RAW/ct-fix.sh | bash"
# 2) Docker + Komodo Periphery
pct push "$ID" "$KEY" /root/.komodo-onboarding.key --perms 600
pct exec "$ID" -- env CONNECT_AS="$NAME" bash -c "curl -fsSL $RAW/komodo-bootstrap.sh | bash"
