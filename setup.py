#!/usr/bin/env python3
"""
NetGuard Setup Script
Installs dependencies and configures the system for network monitoring
"""

import os
import sys
import subprocess
import platform

def run_command(command, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    
    if success:
        print("✓ Requirements installed successfully")
    else:
        print(f"✗ Failed to install requirements: {stderr}")
        return False
    
    return True

def check_admin_privileges():
    """Check if running with administrator privileges"""
    if platform.system() == "Windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

def setup_hosts_file_permissions():
    """Setup permissions for hosts file modification"""
    if platform.system() == "Windows":
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        
        if not os.path.exists(hosts_path):
            print(f"✗ Hosts file not found at {hosts_path}")
            return False
        
        # Check if we can write to hosts file
        try:
            with open(hosts_path, 'a') as f:
                pass
            print("✓ Hosts file is writable")
            return True
        except PermissionError:
            print("✗ Cannot write to hosts file. Please run as administrator.")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "models",
        "data"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")
    
    return True

def setup_proxy_certificate():
    """Setup mitmproxy certificate for HTTPS interception"""
    print("Setting up mitmproxy certificate...")
    
    # Create mitmproxy config directory
    mitmproxy_dir = os.path.expanduser("~/.mitmproxy")
    if not os.path.exists(mitmproxy_dir):
        os.makedirs(mitmproxy_dir)
    
    print("✓ Mitmproxy directory created")
    print("Note: For HTTPS traffic analysis, you'll need to:")
    print("  1. Start the application")
    print("  2. Configure your browser to use 127.0.0.1:8080 as HTTP proxy")
    print("  3. Visit http://mitm.it to install the certificate")
    
    return True

def main():
    """Main setup function"""
    print("NetGuard Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        return False
    
    print(f"✓ Python {sys.version.split()[0]} detected")
    
    # Check admin privileges
    if not check_admin_privileges():
        print("⚠ Warning: Not running as administrator")
        print("  Some features (hosts file modification) may not work")
    else:
        print("✓ Running with administrator privileges")
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Setup hosts file permissions
    if not setup_hosts_file_permissions():
        print("⚠ Warning: Hosts file setup failed")
    
    # Setup proxy certificate
    if not setup_proxy_certificate():
        print("⚠ Warning: Proxy certificate setup failed")
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nTo start NetGuard:")
    print("  python app.py")
    print("\nTo enable dev mode:")
    print("  1. Go to Settings in the web interface")
    print("  2. Enable Developer Mode")
    print("  3. Configure your browser proxy to 127.0.0.1:8080")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)