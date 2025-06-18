#!/bin/bash

# Azure VM Deployment Script for Terrece Lead Forecasting Application
# This script sets up the environment and configures the application to run on port 8503

echo "🌱 Setting up Terrece Lead Forecasting Application on Azure VM"
echo "============================================================"

# Check if running as root (needed for firewall changes)
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script requires sudo privileges for firewall configuration"
    echo "Please run with: sudo bash deploy_azure.sh"
    exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
apt-get update -y

# Install Python and pip if not already installed
echo "🐍 Ensuring Python 3 and pip are installed..."
apt-get install -y python3 python3-pip python3-venv

# Install required system packages for the application
echo "📚 Installing system dependencies..."
apt-get install -y build-essential python3-dev

# Create application user if doesn't exist
if ! id "terrece" &>/dev/null; then
    echo "👤 Creating application user 'terrece'..."
    useradd -m -s /bin/bash terrece
fi

# Get the current directory (where the script is run from)
APP_DIR=$(pwd)
echo "📂 Application directory: $APP_DIR"

# Set proper ownership
chown -R terrece:terrece "$APP_DIR"

# Configure firewall to allow port 8503
echo "🔥 Configuring firewall for port 8503..."

# For Ubuntu/Debian with ufw
if command -v ufw &> /dev/null; then
    ufw allow 8503/tcp
    ufw --force enable
    echo "✅ UFW firewall configured for port 8503"
fi

# For systems with iptables
if command -v iptables &> /dev/null; then
    iptables -A INPUT -p tcp --dport 8503 -j ACCEPT
    # Try to save iptables rules (method varies by system)
    if command -v iptables-save &> /dev/null; then
        iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
    fi
    echo "✅ Iptables configured for port 8503"
fi

# Create virtual environment as terrece user
echo "🐍 Setting up Python virtual environment..."
sudo -u terrece python3 -m venv "$APP_DIR/venv"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
sudo -u terrece "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u terrece "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# Create systemd service file
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/terrece.service << EOF
[Unit]
Description=Terrece Lead Forecasting Application
After=network.target
Wants=network.target

[Service]
Type=exec
User=terrece
Group=terrece
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$APP_DIR/venv/bin/python start_app.py --port 8503 --host 0.0.0.0
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable the service
systemctl daemon-reload
systemctl enable terrece

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🚀 To start the application, run:"
echo "   sudo systemctl start terrece"
echo ""
echo "📊 To check application status:"
echo "   sudo systemctl status terrece"
echo ""
echo "📝 To view application logs:"
echo "   sudo journalctl -u terrece -f"
echo ""
echo "🌐 The application will be available at:"
echo "   http://YOUR_VM_IP:8503"
echo ""
echo "🔧 To stop the application:"
echo "   sudo systemctl stop terrece"
echo ""
echo "⚠️  Remember to:"
echo "   1. Configure your Azure Network Security Group to allow inbound traffic on port 8503"
echo "   2. Replace YOUR_VM_IP with your actual Azure VM public IP address"
echo "   3. Set up your Salesforce credentials in the application interface" 