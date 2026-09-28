#!/usr/bin/env bash
# Codex read-only fleet bootstrap. Run once as root on a Debian/Ubuntu node.
# Safe to store in a private Git repository: it contains only a public key.
set -euo pipefail

readonly CODEX_PUBLIC_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILF5sDZuu6XUgrRM3pi21E6M+3yilSRz/RHhIHzeRzmB codex-fleet-readonly-2026-09-28'

if ! command -v sudo >/dev/null 2>&1; then
  apt-get update
  apt-get install --yes sudo
fi

id codex >/dev/null 2>&1 || useradd --create-home --shell /bin/bash codex
usermod --shell /bin/bash codex

install -d -m 0755 /usr/local/libexec /etc/sudoers.d
install -d -o codex -g codex -m 0700 /home/codex/.ssh

cat >/usr/local/libexec/codex-diagnose <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf '%s\n' 'Allowed: health | docker-status | docker-logs <name> | systemd <unit>'
}
valid_name() { [[ "$1" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$ ]]; }
valid_unit() { [[ "$1" =~ ^[a-zA-Z0-9@_.-]+\.service$ ]]; }

read -r -a words <<<"${SSH_ORIGINAL_COMMAND:-help}"
action=${words[0]:-help}
argument=${words[1]:-}
count=${#words[@]}

case "$action" in
  help|'') usage ;;
  health)
    [[ "$count" -eq 1 ]] || { usage; exit 64; }
    hostnamectl
    printf '\nFilesystem:\n'; df -hT -x tmpfs -x devtmpfs
    printf '\nMemory:\n'; free -h
    printf '\nListening sockets:\n'; ss -tulpen
    ;;
  docker-status)
    [[ "$count" -eq 1 ]] || { usage; exit 64; }
    docker ps --all --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
    ;;
  docker-logs)
    [[ "$count" -eq 2 ]] && valid_name "$argument" || { usage; exit 64; }
    docker logs --tail 200 "$argument"
    ;;
  systemd)
    [[ "$count" -eq 2 ]] && valid_unit "$argument" || { usage; exit 64; }
    systemctl status --no-pager --full "$argument"
    journalctl --no-pager --output=short-iso --lines=100 --unit="$argument"
    ;;
  *) echo 'Command is not permitted.' >&2; usage; exit 64 ;;
esac
EOF
chmod 0755 /usr/local/libexec/codex-diagnose

printf 'command="sudo -n /usr/local/libexec/codex-diagnose",no-agent-forwarding,no-port-forwarding,no-pty,no-user-rc,no-X11-forwarding %s\n' "$CODEX_PUBLIC_KEY" \
  >/home/codex/.ssh/authorized_keys
chown codex:codex /home/codex/.ssh/authorized_keys
chmod 0600 /home/codex/.ssh/authorized_keys

cat >/etc/sudoers.d/codex-diagnose <<'EOF'
codex ALL=(root) NOPASSWD: /usr/local/libexec/codex-diagnose
Defaults!/usr/local/libexec/codex-diagnose env_keep += "SSH_ORIGINAL_COMMAND"
EOF
chmod 0440 /etc/sudoers.d/codex-diagnose
visudo --check --file=/etc/sudoers.d/codex-diagnose
echo 'Codex restricted diagnostic access installed.'
