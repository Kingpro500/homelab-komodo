#!/bin/bash
# Installs Docker CE + Komodo Periphery (systemd) inside a Debian/Ubuntu CT and
# registers it in Komodo Core. Normally started from the Proxmox host by
# scripts/ct-komodo.sh, which sets CONNECT_AS and pushes the onboarding key to
# /root/.komodo-onboarding.key. The key is never stored in this repository.
set -euo pipefail
CONNECT_AS="${CONNECT_AS:?CONNECT_AS mangler, f.eks. pc8-ct126-netalertx}"
KOMODO_VERSION="${KOMODO_VERSION:-v2.3.3}"
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
if command -v docker >/dev/null && docker ps -a --format '{{.Names}}' | grep -qi periphery; then
  die "periphery-container finnes allerede – to agenter på samme CT gir Komodo-løkke"
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

echo "-- Komodo Periphery $KOMODO_VERSION"
run "installasjonsskript hentet" curl -fsSL "https://raw.githubusercontent.com/moghtech/komodo/$KOMODO_VERSION/scripts/setup-periphery.py" -o /root/setup-periphery.py
systemctl stop periphery 2>/dev/null || true
if [ -f /etc/komodo/periphery.config.toml ]; then
  mv /etc/komodo/periphery.config.toml "/etc/komodo/periphery.config.toml.old.$(date +%Y%m%d-%H%M%S)"; ok "gammel config tatt vare på"
fi
run "periphery installert" python3 /root/setup-periphery.py \
  --version "$KOMODO_VERSION" \
  --config-url "https://raw.githubusercontent.com/moghtech/komodo/$KOMODO_VERSION/config/periphery.config.toml" \
  --core-address "$CORE_ADDRESS" \
  --connect-as "$CONNECT_AS" \
  --onboarding-key "$ONBOARDING_KEY" \
  --core-public-keys "$CORE_PUBLIC_KEY"
unset ONBOARDING_KEY; rm -f "$KEYFILE"
systemctl daemon-reload
run "periphery startet" systemctl enable --now periphery
sleep 8
systemctl is-active --quiet periphery && ok "periphery kjører" || die "periphery kjører ikke"
grep -E '^(core_address|connect_as)' /etc/komodo/periphery.config.toml | sed 's/^/        /'
journalctl -u periphery --since "1 minute ago" --no-pager -n 6 | sed 's/^/        /'
echo "== FERDIG: $CONNECT_AS skal nå vises som OK i Komodo"
