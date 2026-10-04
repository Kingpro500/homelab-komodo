#!/bin/bash
# NetBox + Scanopy stack setup for CT102 on the pve node
# Run this INSIDE CT102 (pct exec 102 -- bash /opt/stacks/setup.sh)
#
# This script only stages files on disk. It does NOT create the Komodo stack and
# does NOT deploy anything. A stack only exists once it is registered in Komodo
# and someone clicks Deploy; a container running from `docker compose up` on the
# host is not a Komodo stack. Verify with the Komodo read API, type ListStacks.

set -e

STACKS=(
    "pc8-ct102-netbox"
    "pc8-ct102-scanopy"
)

REPO_URL="https://github.com/Kingpro500/homelab-komodo"
REPO_DIR="/opt/stacks-repo"

echo "=== NetBox + Scanopy staging ==="
echo ""

# 1. Clone repo
if [ ! -d "$REPO_DIR" ]; then
    echo "1. Cloning homelab-komodo repo..."
    git clone "$REPO_URL" "$REPO_DIR"
else
    echo "1. Repo already exists, pulling latest..."
    cd "$REPO_DIR"
    git pull origin main
fi

cd "$REPO_DIR"

# 2. Create stack directories and docker-compose symlinks
for stack in "${STACKS[@]}"; do
    stack_dir="/opt/stacks/$stack"
    compose_src="stacks/$stack/docker-compose.yml"
    
    echo ""
    echo "2. Setting up $stack..."
    
    if [ ! -d "$stack_dir" ]; then
        mkdir -p "$stack_dir"
    fi
    
    # Copy or symlink compose file
    if [ ! -f "$stack_dir/docker-compose.yml" ]; then
        cp "$compose_src" "$stack_dir/docker-compose.yml"
        echo "   ✓ Copied docker-compose.yml"
    fi
    
    # Create .env from .env.example if it doesn't exist
    if [ ! -f "$stack_dir/.env" ]; then
        if [ -f "stacks/$stack/.env.example" ]; then
            cp "stacks/$stack/.env.example" "$stack_dir/.env"
            echo "   ✓ Created .env from template (edit before deploy!)"
        echo "   ⚠  Template values are placeholders. Replace every PASSWORD/KEY before deploying."
        fi
    fi
done

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. In the Komodo UI, create the stack (server pc8-ct102-core):"
echo "   - Name: pc8-ct102-netbox"
echo "     Server: pc8-ct102-core"
echo "     Run dir: /opt/stacks/pc8-ct102-netbox"
echo "     Git: https://github.com/Kingpro500/homelab-komodo (main)"
echo "     Files: stacks/pc8-ct102-netbox/docker-compose.yml"
echo ""
echo "   - Name: pc8-ct102-scanopy"
echo "     (same server/git, different run dir and file path)"
echo ""
echo "2. Replace the placeholder values in /opt/stacks/<stack>/.env with real ones."
echo "   The compose files read every secret from .env via \${VAR:?...}; there are no"
echo "   hardcoded defaults, so compose refuses to start if a value is missing."
echo ""
echo "3. Click Deploy in Komodo for each stack, then verify with docker compose ps."
echo ""
echo "4. Services will be available at:"
echo "   - NetBox: http://10.0.0.117:8001"
echo "   - Scanopy: http://10.0.0.117:8002"
echo ""
echo "Grafana is NOT part of this stack set: it runs on CT109 at http://10.0.0.128:3000."
