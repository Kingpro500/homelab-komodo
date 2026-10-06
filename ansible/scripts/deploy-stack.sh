#!/bin/sh
# deploy-stack.sh — deployer/oppdaterer én Docker-stack INNE i en LXC-CT.
# Skriptet kjøres INNE I CT-en (via pct exec), ikke på noden.
#
# Bruk: deploy-stack.sh <stack_dir> [compose_cmd]
#   stack_dir   : katalog INNE i CT-en der docker-compose.yml ligger
#                 (Komodo-klon: /opt/komodo/stacks/<stack>/<run_directory>/)
#   compose_cmd : "docker compose" (v2, default) eller "docker-compose" (v1)
#
# Flyt: git pull (hvis repo) -> compose config -q (valider) -> pull -> up -d
set -u

STACK_DIR="${1:?stack_dir mangler}"
COMPOSE="${2:-docker compose}"

if [ ! -d "$STACK_DIR" ]; then
  echo "FEIL: katalog finnes ikke: $STACK_DIR"
  exit 2
fi
cd "$STACK_DIR" || exit 2

echo "=== $(hostname) :: $STACK_DIR ==="

# 1) Oppdater repoet hvis det er en git-klon (Komodo bruker dette).
if [ -d .git ]; then
  echo "--- git pull (rebase) ---"
  git fetch --quiet origin 2>&1 | head -5
  git rebase --quiet origin/HEAD 2>&1 | head -5 || git reset --hard --quiet origin/HEAD 2>&1 | head -5
fi

# 2) Velg riktig compose-kommando hvis ikke spesifisert.
if [ -z "${2:-}" ]; then
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
  else
    echo "FEIL: verken 'docker compose' eller 'docker-compose' fins i CT-en"
    exit 2
  fi
fi

# 3) Valider compose-fila (fanger YAML/oppsettfeil før deploy).
echo "--- compose config -q (validering) ---"
if ! $COMPOSE config -q; then
  echo "FEIL: compose config -q mislyktes — stopper før deploøy"
  exit 1
fi

# 4) Hent nye images og re-kjør containere.
echo "--- compose pull ---"
$COMPOSE pull --quiet 2>&1 | tail -5

echo "--- compose up -d ---"
$COMPOSE up -d 2>&1 | tail -15

echo "=== ferdig: $COMPOSE up -d i $STACK_DIR ==="
