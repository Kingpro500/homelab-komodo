#!/bin/bash
# NetBox + Scanopy + Grafana stack setup for Komodo
# Run this on the Komodo host after stacks are created in the UI
# OR manual step-by-step if preferred

set -e

STACKS=(
    "pc8-ct102-netbox"
    "pc8-ct102-scanopy"
    "pc8-ct102-grafana"
)

REPO_URL="https://github.com/Kingpro500/homelab-komodo"
REPO_DIR="/opt/stacks-repo"

echo "=== NetBox + Scanopy + Grafana Setup ==="
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
        fi
    fi
done

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. In Komodo UI, create three new stacks:"
echo "   - Name: pc8-ct102-netbox"
echo "     Server: pc8-ct102-komodo"
echo "     Run dir: /opt/stacks/pc8-ct102-netbox"
echo "     Git: https://github.com/Kingpro500/homelab-komodo (main)"
echo "     Files: stacks/pc8-ct102-netbox/docker-compose.yml"
echo ""
echo "   - Name: pc8-ct102-scanopy"
echo "     (same server/git, different run dir and file path)"
echo ""
echo "   - Name: pc8-ct102-grafana"
echo "     (same server/git, different run dir and file path)"
echo ""
echo "2. After creating each stack in the UI, click Deploy"
echo ""
echo "3. Edit .env files in /opt/stacks/<stack>/ with actual passwords/tokens"
echo ""
echo "4. Services will be available at:"
echo "   - NetBox: http://10.0.0.117:8001"
echo "   - Scanopy: http://10.0.0.117:8002"
echo "   - Grafana: http://10.0.0.117:3000"
