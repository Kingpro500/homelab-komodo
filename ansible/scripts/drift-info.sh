#!/bin/sh
# drift-info.sh — samler kompakt driftsstatus INNE i en LXC-CT.
# Kjøres INNE I CT-en (via pct exec / deploy). Read-only: ingen endringer.
#
# Output: nøkkel=verdi-linjer som Ansible kan presentere.
set -u

echo "=== DRIFT-RAPPORT $(date '+%F %T') ==="
echo "hostname=$(hostname)"

# Oppetid + last
echo "uptime=$(uptime -p 2>/dev/null)"
echo "load=$(cat /proc/loadavg 2>/dev/null | awk '{print $1}')"

# Minne (free-kommando, MB)
if command -v free >/dev/null 2>&1; then
  mem_total=$(free -m 2>/dev/null | awk '/Mem:/{print $2}')
  mem_avail=$(free -m 2>/dev/null | awk '/Mem:/{print $7}')
  echo "mem_total_mb=${mem_total:-?}"
  echo "mem_avail_mb=${mem_avail:-?}"
fi

# Disk (root)
if command -v df >/dev/null 2>&1; then
  echo "disk_root=$(df -h / 2>/dev/null | awk 'NR==2{print $5}') (av $(df -h / 2>/dev/null | awk 'NR==2{print $4}'))"
fi

# Docker: antall containere + status
if command -v docker >/dev/null 2>&1; then
  total=$(docker ps -a 2>/dev/null | tail -n +2 | wc -l)
  running=$(docker ps 2>/dev/null | tail -n +2 | wc -l)
  exclude=$(docker ps 2>/dev/null | grep -cE 'komodo|periphery' || true)
  echo "docker_total=${total:-0}"
  echo "docker_running=${running:-0}"
else
  echo "docker_total=0"
  echo "docker_running=0"
fi
