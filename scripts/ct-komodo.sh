#!/bin/bash
# Run on a Proxmox node:  ct-komodo.sh <ctid> [tjeneste]
#   curl -fsSL https://raw.githubusercontent.com/Kingpro500/homelab-komodo/main/scripts/ct-komodo.sh | bash -s -- 126 netalertx
# Names the Komodo server <node>-ct<id>-<tjeneste>, sets CT DNS in Proxmox, makes sure
# nesting+keyctl are on, runs ct-fix.sh in the CT, then komodo-bootstrap.sh.
# If <navn>/docker-compose.yml exists in the repo, the Komodo stack is created and deployed
# (needs /root/.config/komodo/api.env with KOMODO_URL, KOMODO_API_KEY, KOMODO_API_SECRET).
# Onboarding key is read from /root/.config/komodo/onboarding.key on the node (mode 600).
set -euo pipefail
command -v jq >/dev/null || { apt-get -qq update && apt-get -qq install -y jq; } >/dev/null 2>&1 || { echo "FEIL: jq mangler på noden"; exit 1; }
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
pct exec "$ID" -- env LANG=C.UTF-8 LC_ALL=C.UTF-8 bash -c "printf 'search lan.local\nnameserver 10.0.0.115\nnameserver 10.0.0.118\nnameserver 10.0.0.1\n' >/etc/resolv.conf; command -v curl >/dev/null || { apt-get -qq update && apt-get -qq install -y curl; } >/dev/null; curl -fsSL $RAW/ct-fix.sh | bash"
# 2) Docker + Komodo Periphery (hoppes over hvis CT-en allerede er registrert med samme navn)
if pct exec "$ID" -- sh -c "systemctl is-active --quiet periphery && grep -q '^connect_as = \"$NAME\"' /etc/komodo/periphery.config.toml" 2>/dev/null; then
  echo "  OK    periphery kjører allerede som $NAME – registrering hoppes over"
else
  pct push "$ID" "$KEY" /root/.komodo-onboarding.key --perms 600
  pct exec "$ID" -- env LANG=C.UTF-8 LC_ALL=C.UTF-8 CONNECT_AS="$NAME" bash -c "curl -fsSL $RAW/komodo-bootstrap.sh | bash"
fi

# 3) Komodo-stack fra Git, hvis mappen finnes
REPO=https://raw.githubusercontent.com/Kingpro500/homelab-komodo/main
API=/root/.config/komodo/api.env
IPADDR=$(pct config "$ID" | sed -n 's/^net0:.*ip=\([0-9.]*\).*/\1/p')
if curl -fsI "$REPO/$NAME/docker-compose.yml" >/dev/null 2>&1; then
  if [ -s "$API" ]; then
    set -a; . "$API"; set +a
    kapi(){ curl -fsS -m20 -H "Content-Type: application/json" -H "X-Api-Key: $KOMODO_API_KEY" -H "X-Api-Secret: $KOMODO_API_SECRET" -X POST "$KOMODO_URL/$1" -d "$2"; }
    SID=""
    for i in $(seq 1 30); do
      SID=$(kapi read '{"type":"ListServers","params":{}}' | jq -r --arg n "$NAME" '.[]|select(.name==$n and .info.state=="Ok")|.id' 2>/dev/null || true)
      [ -n "$SID" ] && break; sleep 2
    done
    if [ -z "$SID" ]; then echo "  FEIL  serveren $NAME ble ikke OK i Komodo – stacken er ikke laget"
    else
      BODY=$(jq -nc --arg n "$NAME" --arg s "$SID" '{type:"CreateStack",params:{name:$n,config:{server_id:$s,project_name:$n,auto_pull:true,git_provider:"github.com",git_https:true,repo:"Kingpro500/homelab-komodo",branch:"main",run_directory:$n,file_paths:["docker-compose.yml"]}}}')
      CODE=$(curl -s -o /dev/null -w '%{http_code}' -m20 -H "Content-Type: application/json" -H "X-Api-Key: $KOMODO_API_KEY" -H "X-Api-Secret: $KOMODO_API_SECRET" -X POST "$KOMODO_URL/write" -d "$BODY")
      case "$CODE" in 200) echo "  OK    stack $NAME opprettet i Komodo";; 409) echo "  OK    stack $NAME finnes fra før";; *) echo "  FEIL  CreateStack svarte HTTP $CODE";; esac
      kapi execute "$(jq -nc --arg n "$NAME" '{type:"DeployStack",params:{stack:$n}}')" >/dev/null && echo "  OK    deploy av $NAME startet" || echo "  FEIL  deploy feilet"
    fi
  else
    echo "  MERK  $API mangler – stacken må lages i Komodo for hånd"
  fi
else
  echo "  MERK  ingen mappe $NAME/ i GitHub ennå – lag docker-compose.yml der, og kjør ct-komodo $ID igjen"
fi

# 4) Overvåking – ferdige linjer å legge inn
cat <<SNIP

== Til overvåking (valgfritt, kan legges inn senere)
Smokeping (pc9-ct113-ntopng/smokeping/Targets, under + Services):
++ ${SVC^}
menu = ${SVC}
title = ${NAME} ($IPADDR)
host = $IPADDR

Nettverkskart / INVENTORY: ${NAME} · ${IPADDR} · $(pct config "$ID" | awk '/^cores:/{c=$2}/^memory:/{m=$2}END{print c" kjerne(r), "m" MB"}')
SNIP
