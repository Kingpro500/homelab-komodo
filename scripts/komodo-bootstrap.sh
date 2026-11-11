#!/bin/bash
# Installs Docker CE + Komodo Periphery (Docker-container, templates/lxc-komodo-v2/periphery-compose.yml) inside a Debian/Ubuntu CT and
# registers it in Komodo Core. Normally started from the Proxmox host by
# scripts/ct-komodo.sh, which sets CONNECT_AS and pushes the onboarding key to
# /root/.komodo-onboarding.key. The key is never stored in this repository.
set -euo pipefail
CONNECT_AS="${CONNECT_AS:?CONNECT_AS mangler, f.eks. pc8-ct126-netalertx}"
V=$(curl -fsS -m10 http://10.0.0.117:9120/version 2>/dev/null | tr -d "[:space:]"); KOMODO_VERSION="${KOMODO_VERSION:-v${V:-2.3.3}}"; KOMODO_VERSION="v${KOMODO_VERSION#v}"
CORE_ADDRESS="${CORE_ADDRESS:-http://10.0.0.117:9120}"
CORE_PUBLIC_KEY="${CORE_PUBLIC_KEY:-MCowBQYDK2VuAyEAysGhIUE9ukbCPqQjzedsIownzCgPfCEmJMpQaSXqOGs=}"
KEYFILE=/root/.komodo-onboarding.key
LOG=/var/log/komodo-bootstrap.log; : > "$LOG"
export DEBIAN_FRONTEND=noninteractive
APT="apt-get -qq -o Dpkg::Use-Pty=0"
ok(){ printf '  OK    %s\n' "$1"; }
die(){ printf '  FEIL  %s\n' "$1"; tail -n 15 "$LOG" | sed 's/^/        /'; rm -f "$KEYFILE"; exit 1; }
run(){ local m="$1"; shift; "$@" >>"$LOG" 2>&1 && ok "$m" || die "$m"; }

. /etc/os-release
case "$ID" in debian|ubuntu) ;; *) die "ustøttet distro: $ID";; esac
[ -n "${VERSION_CODENAME:-}" ] || die "fant ikke VERSION_CODENAME"
echo "== Komodo-registrering: $CONNECT_AS ($ID $VERSION_CODENAME) mot $CORE_ADDRESS"
if systemctl list-unit-files periphery.service 2>/dev/null | grep -q periphery; then
  die "systemd-periphery finnes allerede – to agenter på samme CT gir Komodo-løkke (fjern den først)"
fi
ONBOARDING_KEY="${ONBOARDING_KEY:-$(cat "$KEYFILE" 2>/dev/null || true)}"
[ -n "$ONBOARDING_KEY" ] || die "fant ingen onboarding-nøkkel ($KEYFILE)"

echo "-- Docker (logg: $LOG)"
run "grunnpakker" $APT install -y ca-certificates curl python3
install -m 0755 -d /etc/apt/keyrings
run "Docker-nøkkel" curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
printf 'Types: deb\nURIs: https://download.docker.com/linux/%s\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$ID" "$VERSION_CODENAME" "$(dpkg --print-architecture)" > /etc/apt/sources.list.d/docker.sources
run "pakkelister" $APT update
run "Docker installert" $APT install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
run "Docker startet" systemctl enable --now docker
ok "$(docker compose version)"

echo "-- Komodo Periphery $KOMODO_VERSION (Docker)"
PD=/opt/komodo/periphery
install -d -m 0755 /opt/komodo "$PD"
run "compose-mal hentet" curl -fsSL "https://raw.githubusercontent.com/Kingpro500/homelab-komodo/${HOMELAB_REF:-main}/templates/lxc-komodo-v2/periphery-compose.yml" -o "$PD/compose.yml"
sed -i "s#komodo-periphery:[0-9][0-9.]*#komodo-periphery:${KOMODO_VERSION#v}#" "$PD/compose.yml"
printf '%s' "$CORE_PUBLIC_KEY" > "$PD/core.pub"  # uten linjeskift: ellers 'not base64' i Periphery
umask 077
printf 'PERIPHERY_CORE_ADDRESS=%s\nPERIPHERY_CONNECT_AS=%s\nPERIPHERY_ONBOARDING_KEY=%s\n' "$CORE_ADDRESS" "$CONNECT_AS" "$ONBOARDING_KEY" > "$PD/.env"
umask 022
unset ONBOARDING_KEY; rm -f "$KEYFILE"
run "periphery-container startet" docker compose -f "$PD/compose.yml" --env-file "$PD/.env" -p komodo-periphery up -d
for i in $(seq 1 30); do docker logs komodo-periphery 2>&1 | grep -q "Logged in to Komodo Core" && break; sleep 2; done
docker logs komodo-periphery 2>&1 | grep -q "Logged in to Komodo Core" && ok "periphery logget inn i Core" || die "periphery fikk ikke kontakt med Core (docker logs komodo-periphery)"
# Onboarding-nøkkelen er engangs: fjern den fra .env. Identiteten ligger i volumet periphery-data.
sed -i '/^PERIPHERY_ONBOARDING_KEY=/d' "$PD/.env"
docker compose -f "$PD/compose.yml" --env-file "$PD/.env" -p komodo-periphery up -d >>"$LOG" 2>&1 || true
docker logs --tail 4 komodo-periphery 2>&1 | sed 's/^/        /'
echo "== FERDIG: $CONNECT_AS skal nå vises som OK i Komodo"
