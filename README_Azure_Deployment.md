# Terrece Azure VM Deployment Guide

This guide will help you deploy the Terrece Lead Forecasting Application on your Azure VM running on port 8503.

## 🚀 Quick Start

### 1. Prerequisites
- Azure VM with Ubuntu 18.04+ or similar Linux distribution
- SSH access to your Azure VM
- Public IP address assigned to your VM
- sudo privileges on the VM

### 2. Upload Files to Azure VM

Upload all project files to your Azure VM. You can use SCP, SFTP, or git clone:

```bash
# Option 1: Using git (if your repo is on GitHub)
git clone <your-repo-url>
cd Terrace

# Option 2: Using SCP from your local machine
scp -r /path/to/Terrace your-username@your-vm-ip:/home/your-username/
```

### 3. Run the Deployment Script

```bash
# Make the deployment script executable
chmod +x deploy_azure.sh

# Run the deployment script with sudo
sudo bash deploy_azure.sh
```

### 4. Configure Azure Network Security Group

In the Azure Portal:
1. Navigate to your VM's Network Security Group
2. Add an inbound security rule:
   - **Port ranges**: 8503
   - **Protocol**: TCP
   - **Action**: Allow
   - **Priority**: 1000 (or any available priority)
   - **Name**: AllowTerrece8503

### 5. Start the Application

```bash
# Start the service
sudo systemctl start terrece

# Check if it's running
sudo systemctl status terrece

# View logs
sudo journalctl -u terrece -f
```

### 6. Access the Application

Open your web browser and navigate to:
```
http://YOUR_VM_PUBLIC_IP:8503
```

## 📋 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Install Dependencies

```bash
# Update system
sudo apt-get update -y

# Install Python and required packages
sudo apt-get install -y python3 python3-pip python3-venv build-essential python3-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Firewall

```bash
# Using UFW (Ubuntu Firewall)
sudo ufw allow 8503/tcp
sudo ufw enable

# Or using iptables
sudo iptables -A INPUT -p tcp --dport 8503 -j ACCEPT
```

### 3. Start the Application

```bash
# Method 1: Using the startup script
python start_app.py --port 8503 --host 0.0.0.0

# Method 2: Direct Streamlit command
streamlit run terrece.py --server.port 8503 --server.address 0.0.0.0 --server.headless true
```

## 🔧 Configuration

### Streamlit Configuration

The application uses the following configuration (`.streamlit/config.toml`):

```toml
[server]
port = 8503
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 200

[browser]
gatherUsageStats = false
```

### Salesforce Credentials

You can either:

1. **Enter credentials in the web interface** (recommended for security)
2. **Create a credentials.ini file** (for convenience):

```ini
[salesforce]
username = your_salesforce_username
password = your_salesforce_password
security_token = your_security_token
```

⚠️ **Security Note**: If using credentials.ini, ensure it's not accessible publicly and consider using environment variables instead.

## 🔍 Troubleshooting

### Common Issues

1. **Application not accessible externally**
   - Check Azure Network Security Group rules
   - Verify firewall settings on the VM
   - Ensure the application is binding to 0.0.0.0, not localhost

2. **Port 8503 already in use**
   ```bash
   # Check what's using the port
   sudo netstat -tulnp | grep 8503
   
   # Kill the process or use a different port
   python start_app.py --port 8504
   ```

3. **Python package installation issues**
   ```bash
   # Install system dependencies
   sudo apt-get install build-essential python3-dev
   
   # Upgrade pip
   pip install --upgrade pip setuptools wheel
   ```

4. **Permission issues**
   ```bash
   # Fix ownership
   sudo chown -R $USER:$USER /path/to/Terrace
   
   # Fix permissions
   chmod +x start_app.py deploy_azure.sh
   ```

### Checking Application Status

```bash
# If using systemd service
sudo systemctl status terrece
sudo journalctl -u terrece -f

# If running manually
ps aux | grep streamlit
netstat -tulnp | grep 8503
```

### Restarting the Application

```bash
# If using systemd service
sudo systemctl restart terrece

# If running manually
# Kill the process and restart
pkill -f streamlit
python start_app.py --port 8503 --host 0.0.0.0
```

## 📊 Monitoring and Logs

- **Service logs**: `sudo journalctl -u terrece -f`
- **Application logs**: Check the terminal output if running manually
- **System resources**: `htop` or `top` to monitor CPU/memory usage

## 🔒 Security Considerations

1. **Firewall**: Only open port 8503, keep other ports closed
2. **SSH**: Use key-based authentication and disable password authentication
3. **Updates**: Regularly update your VM and application dependencies
4. **Backup**: Regularly backup your application data and configurations
5. **Monitoring**: Set up monitoring and alerting for your application

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the application logs
3. Verify your Azure VM configuration
4. Check network connectivity and firewall rules

For application-specific issues, refer to the Streamlit documentation or the application's main README.md file. 