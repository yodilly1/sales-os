#!/bin/bash
# =============================================================================
# Sales OS - Staging Environment Provisioning Script
# =============================================================================
# This script provisions a new staging server
# Usage: ./infra/scripts/provision-staging.sh <server-ip>
# =============================================================================

set -e

# Configuration
SERVER_IP="${1:-}"
SSH_USER="${SSH_USER:-ubuntu}"
APP_DIR="/opt/sales-os"
DEPLOY_USER="deploy"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "\n${GREEN}>>> $1${NC}\n"
}

print_warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

print_error() {
    echo -e "${RED}Error: $1${NC}"
    exit 1
}

# Validate input
if [ -z "$SERVER_IP" ]; then
    print_error "Usage: $0 <server-ip>"
fi

# SSH helper
run_ssh() {
    ssh -o StrictHostKeyChecking=accept-new "$SSH_USER@$SERVER_IP" "$@"
}

# =============================================================================
# Provisioning Steps
# =============================================================================

print_step "Starting provisioning for $SERVER_IP"

# Update system
print_step "Updating system packages..."
run_ssh << 'REMOTE_SCRIPT'
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    ufw \
    fail2ban
REMOTE_SCRIPT

# Install Docker
print_step "Installing Docker..."
run_ssh << 'REMOTE_SCRIPT'
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

docker --version
docker-compose --version
REMOTE_SCRIPT

# Configure firewall
print_step "Configuring firewall..."
run_ssh << 'REMOTE_SCRIPT'
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable
sudo ufw status
REMOTE_SCRIPT

# Create deploy user
print_step "Creating deploy user..."
run_ssh << 'REMOTE_SCRIPT'
if ! id deploy &>/dev/null; then
    sudo useradd -m -s /bin/bash deploy
    sudo usermod -aG docker deploy
    sudo mkdir -p /home/deploy/.ssh
    sudo cp ~/.ssh/authorized_keys /home/deploy/.ssh/
    sudo chown -R deploy:deploy /home/deploy/.ssh
    sudo chmod 700 /home/deploy/.ssh
    sudo chmod 600 /home/deploy/.ssh/authorized_keys
fi
REMOTE_SCRIPT

# Create application directory
print_step "Setting up application directory..."
run_ssh << REMOTE_SCRIPT
sudo mkdir -p $APP_DIR
sudo chown deploy:deploy $APP_DIR
REMOTE_SCRIPT

# Configure fail2ban
print_step "Configuring fail2ban..."
run_ssh << 'REMOTE_SCRIPT'
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban
REMOTE_SCRIPT

# Setup log rotation
print_step "Configuring log rotation..."
run_ssh << 'REMOTE_SCRIPT'
sudo tee /etc/logrotate.d/sales-os << 'EOF'
/opt/sales-os/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 deploy deploy
}
EOF
REMOTE_SCRIPT

# Install monitoring agent (optional)
print_step "Setting up monitoring..."
run_ssh << 'REMOTE_SCRIPT'
# Install node_exporter for Prometheus (optional)
if [ ! -f /usr/local/bin/node_exporter ]; then
    cd /tmp
    curl -LO https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
    tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
    sudo mv node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
    rm -rf node_exporter-*

    sudo tee /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable node_exporter
    sudo systemctl start node_exporter
fi
REMOTE_SCRIPT

# Create deployment helper script
print_step "Creating deployment helper..."
run_ssh << 'REMOTE_SCRIPT'
sudo tee /opt/sales-os/deploy-helper.sh << 'EOF'
#!/bin/bash
# Deployment helper script

set -e

APP_DIR="/opt/sales-os"
LOG_FILE="$APP_DIR/logs/deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create logs directory
mkdir -p "$APP_DIR/logs"

# Pull latest images
log "Pulling latest images..."
cd "$APP_DIR"
docker-compose pull

# Perform rolling update
log "Starting rolling update..."
docker-compose up -d --remove-orphans

# Wait for health checks
log "Waiting for health checks..."
sleep 10

# Cleanup
log "Cleaning up old images..."
docker image prune -f

log "Deployment completed successfully!"
EOF
sudo chmod +x /opt/sales-os/deploy-helper.sh
sudo chown deploy:deploy /opt/sales-os/deploy-helper.sh
REMOTE_SCRIPT

# Print summary
print_step "Provisioning Complete!"

echo "Server $SERVER_IP has been provisioned successfully."
echo ""
echo "Next steps:"
echo "1. Copy docker-compose.yml to $APP_DIR on the server"
echo "2. Create .env file with production values"
echo "3. Run: docker-compose up -d"
echo ""
echo "SSH access: ssh deploy@$SERVER_IP"
