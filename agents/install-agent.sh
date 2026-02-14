#!/bin/bash

# NOCbRAIN Agent Installation Script
# Supports: Ubuntu, Debian, CentOS, RHEL, Fedora

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_VERSION="1.0.0"
AGENT_USER="nocbrain"
AGENT_DIR="/opt/nocbrain-agent"
AGENT_SERVICE="/etc/systemd/system/nocbrain-agent.service"
CONFIG_FILE="/etc/nocbrain-agent/config.json"

# Functions
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "=================================="
    echo " NOCbRAIN Agent Installer"
    echo " Version: $AGENT_VERSION"
    echo "=================================="
    echo -e "${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [[ -f /etc/lsb-release ]]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [[ -f /etc/debian_version ]]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    else
        print_error "Unable to detect operating system"
        exit 1
    fi
    
    print_status "Detected OS: $OS $VER"
}

install_dependencies() {
    print_status "Installing dependencies..."
    
    case $OS in
        "Ubuntu"* | "Debian"*)
            apt-get update
            apt-get install -y python3 python3-pip python3-venv curl wget systemd
            ;;
        "CentOS"* | "Red Hat"* | "Fedora"*)
            if command -v dnf &> /dev/null; then
                dnf update -y
                dnf install -y python3 python3-pip curl wget systemd
            else
                yum update -y
                yum install -y python3 python3-pip curl wget systemd
            fi
            ;;
        *)
            print_error "Unsupported operating system: $OS"
            exit 1
            ;;
    esac
}

create_user() {
    print_status "Creating NOCbRAIN user..."
    
    if ! id "$AGENT_USER" &>/dev/null; then
        useradd -r -s /bin/false -d $AGENT_DIR $AGENT_USER
        print_status "Created user: $AGENT_USER"
    else
        print_warning "User $AGENT_USER already exists"
    fi
}

create_directories() {
    print_status "Creating directories..."
    
    mkdir -p $AGENT_DIR
    mkdir -p $(dirname $CONFIG_FILE)
    mkdir -p /var/log/nocbrain-agent
    mkdir -p /var/run/nocbrain-agent
    
    # Set ownership
    chown -R $AGENT_USER:$AGENT_USER $AGENT_DIR
    chown -R $AGENT_USER:$AGENT_USER $(dirname $CONFIG_FILE)
    chown -R $AGENT_USER:$AGENT_USER /var/log/nocbrain-agent
    chown -R $AGENT_USER:$AGENT_USER /var/run/nocbrain-agent
}

install_agent() {
    print_status "Installing NOCbRAIN agent..."
    
    # Download agent
    cd /tmp
    wget -O nocbrain-agent.py "https://raw.githubusercontent.com/conformist77/nocbrain/main/agents/nocbrain-agent.py"
    
    # Install to agent directory
    cp nocbrain-agent.py $AGENT_DIR/
    chmod +x $AGENT_DIR/nocbrain-agent.py
    
    # Install Python dependencies
    sudo -u $AGENT_USER python3 -m pip install --user psutil requests cryptography
    
    # Create symlink
    ln -sf $AGENT_DIR/nocbrain-agent.py /usr/local/bin/nocbrain-agent
    
    print_status "Agent installed successfully"
}

create_config() {
    print_status "Creating configuration file..."
    
    if [[ ! -f $CONFIG_FILE ]]; then
        cat > $CONFIG_FILE << EOF
{
  "server_url": "https://api.nocbrain.com",
  "api_key": "YOUR_API_KEY_HERE",
  "agent_id": "$(hostname)-$(date +%s)",
  "collection_interval": 60,
  "encryption_enabled": true,
  "compression_enabled": true
}
EOF
        print_status "Configuration file created: $CONFIG_FILE"
        print_warning "Please edit $CONFIG_FILE and set your API key"
    else
        print_warning "Configuration file already exists"
    fi
    
    chown $AGENT_USER:$AGENT_USER $CONFIG_FILE
    chmod 600 $CONFIG_FILE
}

create_systemd_service() {
    print_status "Creating systemd service..."
    
    cat > $AGENT_SERVICE << EOF
[Unit]
Description=NOCbRAIN Monitoring Agent
After=network.target

[Service]
Type=simple
User=$AGENT_USER
Group=$AGENT_USER
WorkingDirectory=$AGENT_DIR
ExecStart=/usr/bin/python3 $AGENT_DIR/nocbrain-agent.py --config $CONFIG_FILE
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Systemd service created"
}

enable_service() {
    print_status "Enabling and starting NOCbRAIN agent..."
    
    systemctl enable nocbrain-agent
    systemctl start nocbrain-agent
    
    # Check status
    if systemctl is-active --quiet nocbrain-agent; then
        print_status "NOCbRAIN agent is running"
    else
        print_error "Failed to start NOCbRAIN agent"
        systemctl status nocbrain-agent
        exit 1
    fi
}

setup_firewall() {
    print_status "Configuring firewall..."
    
    # Check if firewall is running
    if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
        # UFW (Ubuntu)
        print_status "Configuring UFW firewall rules..."
        # Agent typically uses outbound connections only
        print_warning "Please ensure outbound HTTPS (443) is allowed"
    elif command -v firewall-cmd &> /dev/null && firewall-cmd --state &> /dev/null; then
        # firewalld (CentOS/RHEL)
        print_status "Configuring firewalld rules..."
        # Agent typically uses outbound connections only
        print_warning "Please ensure outbound HTTPS (443) is allowed"
    else
        print_warning "No active firewall detected"
    fi
}

show_status() {
    print_status "Installation completed successfully!"
    echo ""
    echo "Agent Information:"
    echo "  - Installation directory: $AGENT_DIR"
    echo "  - Configuration file: $CONFIG_FILE"
    echo "  - Log directory: /var/log/nocbrain-agent"
    echo "  - Service name: nocbrain-agent"
    echo ""
    echo "Management Commands:"
    echo "  - Start service: systemctl start nocbrain-agent"
    echo "  - Stop service: systemctl stop nocbrain-agent"
    echo "  - Restart service: systemctl restart nocbrain-agent"
    echo "  - Check status: systemctl status nocbrain-agent"
    echo "  - View logs: journalctl -u nocbrain-agent -f"
    echo ""
    echo "Next Steps:"
    echo "  1. Edit configuration: nano $CONFIG_FILE"
    echo "  2. Set your API key"
    echo "  3. Restart service: systemctl restart nocbrain-agent"
    echo ""
}

# Main installation flow
main() {
    print_header
    check_root
    detect_os
    install_dependencies
    create_user
    create_directories
    install_agent
    create_config
    create_systemd_service
    setup_firewall
    enable_service
    show_status
}

# Handle command line arguments
case "${1:-}" in
    "uninstall")
        print_status "Uninstalling NOCbRAIN agent..."
        systemctl stop nocbrain-agent || true
        systemctl disable nocbrain-agent || true
        rm -f $AGENT_SERVICE
        systemctl daemon-reload
        userdel -f $AGENT_USER || true
        rm -rf $AGENT_DIR
        rm -rf $(dirname $CONFIG_FILE)
        rm -rf /var/log/nocbrain-agent
        rm -f /usr/local/bin/nocbrain-agent
        print_status "NOCbRAIN agent uninstalled"
        ;;
    "update")
        print_status "Updating NOCbRAIN agent..."
        systemctl stop nocbrain-agent
        install_agent
        systemctl start nocbrain-agent
        print_status "NOCbRAIN agent updated"
        ;;
    *)
        main
        ;;
esac
