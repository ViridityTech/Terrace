#!/usr/bin/env python3
"""
Version information for Terrece application
"""

import subprocess
import datetime
import os

def get_git_version():
    """Get version from git commit info"""
    try:
        # Get the latest commit hash and timestamp
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], 
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        commit_date = subprocess.check_output(
            ["git", "show", "-s", "--format=%ci", "HEAD"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL
        ).decode().strip()
        
        # Format: YYYY-MM-DD-HHMMSS-hash
        date_part = datetime.datetime.strptime(commit_date[:19], "%Y-%m-%d %H:%M:%S")
        version = f"{date_part.strftime('%Y.%m.%d.%H%M%S')}-{commit_hash}"
        
        return version, commit_date, commit_hash
        
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        # Fallback to manual version if git is not available
        manual_version = "2025.06.18.001"  # Update this manually when needed
        return manual_version, "Manual version", "no-git"

def get_version_info():
    """Get complete version information"""
    version, commit_date, commit_hash = get_git_version()
    
    return {
        "version": version,
        "commit_date": commit_date,
        "commit_hash": commit_hash,
        "build_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Get version at module import
VERSION_INFO = get_version_info()
VERSION = VERSION_INFO["version"]

if __name__ == "__main__":
    info = get_version_info()
    print(f"Terrece Version: {info['version']}")
    print(f"Commit Date: {info['commit_date']}")
    print(f"Commit Hash: {info['commit_hash']}")
    print(f"Build Time: {info['build_time']}") 