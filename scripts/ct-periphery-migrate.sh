#!/bin/bash
# Run on a Proxmox node: ct-periphery-migrate <ctid> [nytt-servernavn]
# Moves a CT from Periphery-in-Docker (old standard) to systemd-Periphery (new standard)
# WITHOUT changing its identity: the container's private key and root directory
# (/opt/komodo) are reused, so Core sees the same server and all stacks/paths stay.
# App containers keep running. Automatic rollback if the server is not Ok within 90 s.
# Optional new name: the Komodo server is renamed first (stacks follow the server id).
set -euo pipefail
command -v jq >/dev/null || { apt-get -qq update && apt-get -qq install -y jq; } >/dev/null 2>&1 || { echo "FEIL: jq mangler på noden"; exit 1; }
ID="${1:?Bruk: ct-periphery-migrate <ctid> [nytt-servernavn]}"; NEW="${2:-}"
VER=v2.3.3; CORE=http://10.0.0.117:9120
CORE_PUB="MCowBQYDK2VuAyEAysGhIUE9ukbCPqQjzedsIownzCgPfCEmJMpQaSXqOGs="
API=/root/.config/komodo/api.env
ok(){ printf '  OK    %s\n' "$1"; }; die(){ printf '  FEIL  %s\n' "$1"; exit 1; }
[ -s "$API" ] || die "mangler $API"; set -a; . "$API"; set +a
kapi(){ curl -fsS -m20 -H "Content-Type: application/json" -H "X-Api-Key: $KOMODO_API_KEY" -H "X-Api-Secret: $KOMODO_API_SECRET" -X POST "$KOMODO_URL/$1" -d "$2"; }
X(){ pct exec "$ID" -- env LANG=C.UTF-8 LC_ALL=C.UTF-8 sh -c "$1"; }

C=$(X "docker ps -a --format '{{.Names}}' | grep -i periphery | head -1" || true)
[ -n "$C" ] || die "fant ingen Periphery-container i CT $ID (allerede migrert?)"
OLD=$(X "docker inspect $C --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^PERIPHERY_CONNECT_AS=//p'")
ROOTDIR=$(X "docker inspect $C --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^PERIPHERY_ROOT_DIRECTORY=//p'"); ROOTDIR=${ROOTDIR:-/etc/komodo}
KEYSRC=$(X "docker inspect $C --format '{{range .Mounts}}{{if eq .Destination \"/config/keys\"}}{{.Source}}{{end}}{{end}}'")
[ -n "$KEYSRC" ] || KEYSRC=$(X "docker inspect $C --format '{{range .Mounts}}{{if eq .Destination \"/config\"}}{{.Source}}{{end}}{{end}}'")/keys
[ -n "$OLD" ] || die "container mangler PERIPHERY_CONNECT_AS"
X "test -s $KEYSRC/periphery.key" || die "fant ikke privat nøkkel i $KEYSRC"
NAME="${NEW:-$OLD}"
echo "== CT $ID: $C ($OLD) -> systemd-Periphery som $NAME, root $ROOTDIR"
SID=$(kapi read '{"type":"ListServers","params":{}}' | jq -r --arg n "$OLD" '.[]|select(.name==$n)|.id')
[ -n "$SID" ] || die "fant ikke server $OLD i Komodo"

rollback(){
  echo "  ...   ruller tilbake"
  X "systemctl disable --now periphery 2>/dev/null; docker update --restart=unless-stopped $C >/dev/null; docker start $C >/dev/null" || true
  [ "$NAME" != "$OLD" ] && kapi write "$(jq -nc --arg i "$SID" --arg n "$OLD" '{type:"RenameServer",params:{id:$i,name:$n}}')" >/dev/null || true
  die "migrering feilet – gammel container er startet igjen"
}

X "command -v python3 >/dev/null && command -v curl >/dev/null" || X "apt-get -qq update && apt-get -qq install -y python3 curl >/dev/null" || die "kunne ikke installere python3/curl (sjekk DNS/apt i CT-en, kjør ct-fix)"
X "curl -fsSL https://raw.githubusercontent.com/moghtech/komodo/$VER/scripts/setup-periphery.py -o /root/setup-periphery.py" || die "fikk ikke hentet setup-periphery.py"
X "python3 /root/setup-periphery.py --version $VER --config-url https://raw.githubusercontent.com/moghtech/komodo/$VER/config/periphery.config.toml --core-address $CORE --connect-as $NAME --core-public-keys $CORE_PUB >/var/log/periphery-migrate.log 2>&1" || die "setup-periphery.py feilet (se /var/log/periphery-migrate.log i CT-en)"
X "systemctl stop periphery 2>/dev/null; mkdir -p /etc/komodo/keys && cp $KEYSRC/periphery.key $KEYSRC/periphery.pub /etc/komodo/keys/ && chmod 600 /etc/komodo/keys/*"
X "sed -i 's#^root_directory = .*#root_directory = \"$ROOTDIR\"#' /etc/komodo/periphery.config.toml && grep -q '^root_directory = \"$ROOTDIR\"' /etc/komodo/periphery.config.toml" || die "kunne ikke sette root_directory"
ok "systemd-Periphery $VER installert med samme nøkkel og root $ROOTDIR"

if [ "$NAME" != "$OLD" ]; then
  kapi write "$(jq -nc --arg i "$SID" --arg n "$NAME" '{type:"RenameServer",params:{id:$i,name:$n}}')" >/dev/null || die "RenameServer feilet"
  ok "Komodo-server omdøpt $OLD -> $NAME"
fi
X "docker update --restart=no $C >/dev/null && docker stop $C >/dev/null" || rollback
X "systemctl daemon-reload && systemctl enable --now periphery" || rollback
ok "gammel container stoppet (beholdt, restart=no), systemd-Periphery startet"
for i in $(seq 1 45); do
  ST=$(kapi read '{"type":"ListServers","params":{}}' | jq -r --arg i "$SID" '.[]|select(.id==$i)|.info.state' 2>/dev/null || true)
  [ "$ST" = Ok ] && break; sleep 2
done
[ "${ST:-}" = Ok ] || rollback
ok "$NAME er Ok i Komodo"
X "docker ps --format '        {{.Names}}: {{.Status}}' | grep -v periphery" || true
echo "== FERDIG: $NAME kjører nå systemd-Periphery. Gammel container '$C' er stoppet og kan fjernes senere."
