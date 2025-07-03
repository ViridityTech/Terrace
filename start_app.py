#!/usr/bin/env python3
"""
Startup script for Terrece Lead Forecasting Application on Azure VM
"""

import subprocess
import sys
import os
import argparse

# Import version info
try:
    from version import VERSION_INFO
except ImportError:
    VERSION_INFO = {
        "version": "unknown",
        "commit_date": "unknown", 
        "commit_hash": "unknown",
        "build_time": "unknown"
    }

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import streamlit
        import pandas
        import numpy
        import matplotlib
        import statsmodels
        import simple_salesforce
        print("✅ All required packages are available")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements with: pip install -r requirements.txt")
        return False

def start_streamlit_app(port=8503, host="0.0.0.0"):
    """Start the Streamlit application"""
    
    print(f"🚀 Starting Terrece Lead Forecasting Application...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌐 Access URL: http://{host}:{port}")
    print(f"📦 Version: {VERSION_INFO['version']}")
    print(f"📅 Commit Date: {VERSION_INFO['commit_date']}")
    print(f"🔗 Commit Hash: {VERSION_INFO['commit_hash']}")
    print(f"🕐 Build Time: {VERSION_INFO['build_time']}")
    print("=" * 60)
    
    # Ensure required directories exist
    os.makedirs("forecast_results", exist_ok=True)
    os.makedirs("forecast_visuals", exist_ok=True)
    os.makedirs(".streamlit", exist_ok=True)
    
    # Start Streamlit with custom configuration
    cmd = [
        sys.executable, "-m", "streamlit", "run", "terrece.py",
        "--server.port", str(port),
        "--server.address", host,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Start Terrece Lead Forecasting Application")
    parser.add_argument("--port", "-p", type=int, default=8503, help="Port to run the application on (default: 8503)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address to bind to (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    print("🌱 Terrece - Orchard's Lead Forecasting Agent")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    # Check if we're in the correct directory
    if not os.path.exists("terrece.py"):
        print("❌ Error: terrece.py not found in current directory")
        print("Please run this script from the Terrace project directory")
        sys.exit(1)
    
    start_streamlit_app(args.port, args.host)

if __name__ == "__main__":
    main() 